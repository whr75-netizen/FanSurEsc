"""Local three-field UI and subscription browser bridge; no agent coordinator."""
from __future__ import annotations

import argparse
import base64
from email.parser import BytesParser
from email import policy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import threading
import time
from urllib.parse import parse_qs, unquote, urlparse
import uuid
import zipfile

from runtime import APP_ROOT, RUNS_ROOT, configure, settings
from pipeline import PipelinePaused, atomic_json, continue_pipeline, image_prompt, save_browser_image, subscription_credential, validate_request

PORT = 8765
LABELS = {'image': '원본 이미지', 'video': '원본 영상', 'prepared': '프레임 목록', 'sheet': 'PNG 시트', 'gif': 'GIF', 'webp': 'WebP', 'metadata': 'JSON', 'zip': 'ZIP'}
INPUT_EXTENSIONS = {'image': {'.png', '.jpg', '.jpeg', '.webp'}, 'video': {'.mp4', '.webm', '.mov'}, 'frames': {'.png'}}


class Coordinator:
    def __init__(self, cfg=None, runs_root=RUNS_ROOT):
        self.cfg = configure(cfg or settings())
        self.runs_root = Path(runs_root)
        self.runs_root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.jobs = {}
        self.active = None
        self.latest = None
        self.inputs = {}
        self.last_inputs = {}
        self.watch_root = self.runs_root / 'Inbox'
        self.watch = {'enabled': False, 'root': str(self.watch_root), 'detail': '폴더 감시 OFF'}
        self.watch_spec = {}
        self.observed = {}
        seen_path = self.runs_root / 'watch-seen.json'
        try:
            self.seen = set(json.loads(seen_path.read_text(encoding='utf-8')))
        except (OSError, ValueError):
            self.seen = set()
        for name in ('images', 'videos', 'frames'):
            (self.watch_root / name).mkdir(parents=True, exist_ok=True)
        self.restore()
        threading.Thread(target=self.watch_loop, daemon=True).start()

    def restore(self):
        """A restart never submits to either provider; saved files can be resumed."""
        for directory in self.runs_root.iterdir():
            if not directory.is_dir() or not re.fullmatch(r'[a-f0-9]{32}', directory.name):
                continue
            try:
                job = json.loads((directory / 'job.json').read_text(encoding='utf-8'))
                spec = json.loads((directory / 'request.json').read_text(encoding='utf-8'))
                if job.get('id') != directory.name or not isinstance(job.get('started_at'), (int, float)):
                    continue
            except (OSError, ValueError, TypeError):
                continue
            job.update(directory=str(directory), spec=spec, token=secrets.token_urlsafe(32))
            self.jobs[job['id']] = job
            if job.get('status') == 'running':
                self.fail(job, '프로그램이 중단되었습니다. 저장된 파일부터만 재개할 수 있으며 생성 요청은 자동 반복하지 않습니다.')
            if self.latest is None or job['started_at'] > self.jobs[self.latest]['started_at']:
                self.latest = job['id']
        for job in sorted(self.jobs.values(), key=lambda item: item['started_at']):
            self.collect_inputs(job)

    def persist(self, job):
        # The browser pairing token is memory-only and never a service credential.
        atomic_json(Path(job['directory']) / 'job.json', {k: v for k, v in job.items() if k != 'token'})

    def state(self, ident=None):
        with self.lock:
            job = self.jobs.get(ident or self.latest)
            if not job:
                return {'status': 'idle', 'connection': 'ChatGPT 웹 · Grok 구독', 'watch': dict(self.watch), 'available': {k: k in self.last_inputs for k in INPUT_EXTENSIONS}}
            if job['status'] == 'running' and job['stage'] == 'image':
                elapsed = time.time() - job['started_at']
                if not job.get('browser_tab') and elapsed > 45:
                    self.fail(job, '브라우저 확장이 연결되지 않았습니다. 확장 설치 안내를 확인해 주세요. 생성 요청은 보내지 않았습니다.')
                elif elapsed > 960:
                    self.fail(job, '이미지 파일 전달 대기가 만료되었습니다. 기존 ChatGPT 작업 탭을 확인해 주세요. 자동 재생성하지 않습니다.')
            out = {k: v for k, v in job.items() if k not in ('token', 'spec', 'directory', 'worker')}
            out['elapsed_seconds'] = round((job.get('finished_at') or time.time()) - job['started_at'], 1)
            out['connection'] = 'ChatGPT 웹 · Grok 구독'
            out['watch'] = dict(self.watch)
            out['available'] = {k: k in self.last_inputs for k in INPUT_EXTENSIONS}
            return out

    def start(self, payload):
        with self.lock:
            if self.active:
                raise ValueError('다른 작업이 실행 중입니다.')
            requested_mode = payload.get('mode', 'all')
            required_kind = {'video': 'image', 'frames': 'video', 'pixel': 'frames'}.get(requested_mode)
            input_id = payload.get('input') or self.last_inputs.get(required_kind)
            entry = self.inputs.get(input_id)
            if required_kind and (not entry or entry['kind'] != required_kind):
                raise ValueError('이 단계의 입력 파일을 선택하거나 이전 단계부터 실행해 주세요.')
            if payload.get('input') and entry is None:
                raise ValueError('파일 입력이 만료됐습니다. 다시 선택해 주세요.')
            mode = 'all' if self.watch['enabled'] else requested_mode
            kind = entry['kind'] if entry else None
            needs_image = mode in ('image', 'all') and kind is None
            needs_video = mode in ('video', 'all') and kind not in ('video', 'frames')
            spec = validate_request(dict(payload, mode=mode), require_gpt=needs_image, require_grok=needs_video)
            if needs_video:
                subscription_credential()
            ident = uuid.uuid4().hex
            directory = self.runs_root / ident
            directory.mkdir()
            if entry:
                if kind == 'image':
                    from PIL import Image
                    with Image.open(entry['paths'][0]) as source:
                        source.save(directory / 'source.png', format='PNG')
                elif kind == 'video':
                    shutil.copy2(entry['paths'][0], directory / 'clip.mp4')
                else:
                    if len(entry['paths']) == 1 and Path(entry['paths'][0]).suffix == '.json':
                        spec['prepared_input'] = entry['paths'][0]
                    else:
                        frame_dir = directory / 'input-frames'
                        frame_dir.mkdir()
                        copied = []
                        for index, path in enumerate(entry['paths']):
                            target = frame_dir / f'frame-{index:02d}.png'
                            shutil.copy2(path, target)
                            copied.append(str(target))
                        spec['prepared_input'] = copied
                    spec['duration'] = entry.get('duration', 1.0)
            atomic_json(directory / 'request.json', spec)
            job = {'id': ident, 'token': secrets.token_urlsafe(32), 'spec': spec,
                   'directory': str(directory), 'status': 'running', 'stage': 'image' if needs_image else 'queued',
                   'detail': 'ChatGPT 확장 연결 대기' if needs_image else '저장된 입력부터 실행합니다.',
                   'started_at': time.time(), 'timings_seconds': {}, 'resumable': False,
                   'browser_submitted': False, 'stop_requested': False, 'mode': mode}
            self.jobs[ident] = job
            self.active = self.latest = ident
            self.persist(job)
            if needs_image:
                self.open_browser(job)
            else:
                threading.Thread(target=self.work, args=(job,), daemon=True).start()
            return self.state(ident)

    def register_input(self, kind, paths, duration=1.0):
        ident = uuid.uuid4().hex
        self.inputs[ident] = {'kind': kind, 'paths': [str(path) for path in paths], 'duration': duration}
        self.last_inputs[kind] = ident
        return ident

    def collect_inputs(self, job):
        directory = Path(job['directory'])
        for kind, name in (('image', 'source.png'), ('video', 'clip.mp4')):
            if (directory / name).is_file():
                self.register_input(kind, [directory / name])
        prepared = job.get('artifacts', {}).get('prepared')
        saved_frames = directory / 'frames-result.json'
        if not prepared and saved_frames.is_file():
            prepared = json.loads(saved_frames.read_text(encoding='utf-8')).get('files', {}).get('manifest')
        if prepared and Path(prepared).is_file():
            self.register_input('frames', [prepared])

    def upload(self, content_type, data):
        message = BytesParser(policy=policy.default).parsebytes(('Content-Type: ' + content_type + '\r\nMIME-Version: 1.0\r\n\r\n').encode() + data)
        kind = None
        files = []
        for part in message.iter_parts():
            if part.get_param('name', header='content-disposition') == 'kind':
                kind = part.get_content().strip()
            elif part.get_filename():
                files.append((Path(part.get_filename()).name, part.get_payload(decode=True)))
        if kind not in INPUT_EXTENSIONS or not files or len(files) > (16 if kind == 'frames' else 1):
            raise ValueError('이미지·영상은 1개, PNG 프레임은 1–16개를 선택해 주세요.')
        directory = self.runs_root / 'Uploads' / uuid.uuid4().hex
        directory.mkdir(parents=True)
        paths = []
        for index, (name, data) in enumerate(sorted(files)):
            suffix = Path(name).suffix.lower()
            if suffix not in INPUT_EXTENSIONS[kind] or not data:
                raise ValueError('지원하지 않는 파일 형식이거나 빈 파일입니다.')
            path = directory / f'{index:02d}{suffix}'
            temp = path.with_suffix(path.suffix + '.part')
            temp.write_bytes(data)
            temp.replace(path)
            paths.append(path)
        with self.lock:
            return {'input': self.register_input(kind, paths)}

    def set_watch(self, payload):
        with self.lock:
            if payload.get('enabled'):
                self.watch_spec = validate_request(payload.get('spec', {}), require_gpt=False, require_grok=False)
            elif self.watch['enabled'] and self.active:
                job = self.jobs[self.active]
                job['stop_requested'] = True
                job['detail'] = '전체 루틴 OFF · 현재 구간의 파일 저장 후 멈춥니다.'
                self.persist(job)
            self.watch.update(enabled=bool(payload.get('enabled')), detail='새 파일 저장 완료를 기다립니다.' if payload.get('enabled') else '폴더 감시 OFF')
            return self.state()

    def stop(self):
        with self.lock:
            self.watch.update(enabled=False, detail='중단 요청 · 폴더 감시 OFF')
            if self.active:
                job = self.jobs[self.active]
                job['stop_requested'] = True
                job['detail'] = '현재 구간의 파일 저장 후 중단합니다. 원격 생성 요청은 다시 보내지 않습니다.'
                self.persist(job)
            return self.state()

    def watch_loop(self):
        """One-second local file poll, only while ON; no remote or AI calls here."""
        while True:
            time.sleep(1)
            with self.lock:
                if not self.watch['enabled'] or self.active:
                    continue
            try:
                batches = []
                for kind, name in (('image', 'images'), ('video', 'videos')):
                    batches.extend((kind, [p]) for p in sorted((self.watch_root / name).iterdir()) if p.is_file() and p.suffix.lower() in INPUT_EXTENSIONS[kind])
                frames = self.watch_root / 'frames'
                for folder in [frames] + sorted(p for p in frames.iterdir() if p.is_dir()):
                    paths = sorted(folder.glob('*.png'))
                    if len(paths) == self.watch_spec.get('frame_count'):
                        batches.append(('frames', paths))
                for kind, paths in batches:
                    fingerprint = json.dumps([(str(p), p.stat().st_size, p.stat().st_mtime_ns) for p in paths])
                    if fingerprint in self.seen:
                        continue
                    if time.monotonic() - self.observed.setdefault(fingerprint, time.monotonic()) < 2:
                        continue
                    with self.lock:
                        if not self.watch['enabled'] or self.active:
                            break
                        self.seen.add(fingerprint)
                        atomic_json(self.runs_root / 'watch-seen.json', sorted(self.seen))
                        ident = self.register_input(kind, paths)
                        self.start(dict(self.watch_spec, mode='all', input=ident))
                        self.watch['detail'] = '새 입력을 실행 중입니다. 같은 파일은 반복하지 않습니다.'
                    break
            except (Exception, SystemExit) as exc:
                with self.lock:
                    self.watch.update(enabled=False, detail=f'폴더 감시 중단: {exc}')

    def open_browser(self, job):
        claim = base64.urlsafe_b64encode(json.dumps({'id': job['id'], 'token': job['token'], 'port': PORT}).encode()).decode().rstrip('=')
        chrome = Path(self.cfg['chrome'])
        if not chrome.is_file():
            self.fail(job, 'Chrome 실행 파일을 찾지 못했습니다. settings.local.json의 chrome 경로를 확인하세요.')
            return
        subprocess.Popen([str(chrome), 'https://chatgpt.com/images/#sprite-pipeline=' + claim],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def browser_job(self, payload):
        job = self.jobs.get(payload.get('id'))
        if not job or not secrets.compare_digest(str(payload.get('token', '')), job['token']):
            raise PermissionError('브라우저 연결 토큰이 일치하지 않습니다.')
        tab = payload.get('tab_id')
        if isinstance(tab, bool) or not isinstance(tab, int) or tab < 0:
            raise PermissionError('브라우저 탭 ID가 유효하지 않습니다.')
        if job.get('browser_tab') is not None and job['browser_tab'] != tab:
            raise PermissionError('이 작업은 이미 다른 브라우저 탭에 연결됐습니다.')
        return job

    def claim(self, payload):
        with self.lock:
            job = self.browser_job(payload)
            if job['status'] != 'running' or job['stage'] != 'image':
                raise ValueError('현재 이미지 입력을 기다리는 작업이 아닙니다.')
            job['browser_tab'] = payload['tab_id']
            self.persist(job)
            return {'prompt': image_prompt(job['spec']), 'status': 'submitted' if job['browser_submitted'] else 'ready'}

    def event(self, payload):
        with self.lock:
            job = self.browser_job(payload)
            if job['status'] != 'running' or job['stage'] != 'image':
                return {'ok': True, 'ignored': 'image stage already ended'}
            stage = payload.get('stage')
            if stage == 'submitted':
                job['browser_submitted'] = True
                job['detail'] = 'ChatGPT 이미지 생성 중입니다. 확장이 완료 파일을 전달합니다.'
            elif stage == 'failed':
                self.fail(job, str(payload.get('detail', '브라우저 연결 실패'))[:2000])
                return {'ok': True}
            else:
                job['detail'] = str(payload.get('detail', '이미지 생성 대기'))[:1000]
            self.persist(job)
            return {'ok': True}

    def image_result(self, payload):
        with self.lock:
            job = self.browser_job(payload)
            if job['status'] != 'running' or job['stage'] != 'image':
                raise ValueError('중복 또는 만료된 이미지 결과입니다.')
            directory = Path(job['directory'])
            save_browser_image(payload.get('image_base64'), directory / 'source.png')
            page = urlparse(str(payload.get('source_url', '')))
            atomic_json(directory / 'image-report.json', {
                'provider': 'chatgpt-browser-subscription', 'image': 'source.png',
                'page': f'{page.scheme}://{page.netloc}{page.path}' if page.hostname == 'chatgpt.com' else None,
                'elapsed_seconds': round(time.time() - job['started_at'], 3),
            })
            job['timings_seconds']['image'] = round(time.time() - job['started_at'], 3)
            job['stage'] = 'canvas'
            self.persist(job)
            threading.Thread(target=self.work, args=(job,), daemon=True).start()
            return {'ok': True, 'saved': True}

    def notify(self, job, stage, detail):
        with self.lock:
            if stage != 'done':
                job['stage'], job['detail'] = stage, detail
                self.persist(job)

    def fail(self, job, message):
        with self.lock:
            directory = Path(job['directory'])
            job.update(status='failed', failed_stage=job['stage'], stage='failed', error=str(message)[:3000], finished_at=time.time(),
                       resumable=(directory / 'source.png').exists() or (directory / 'clip.mp4').exists() or bool(job['spec'].get('prepared_input')))
            self.active = None
            self.collect_inputs(job)
            self.persist(job)

    def finish(self, job, result, *, paused=False):
        with self.lock:
            artifacts = dict(result.get('files', {}))
            if 'manifest' in artifacts:
                artifacts['prepared'] = artifacts['manifest']
            frames = artifacts.get('keyed_frames')
            if frames and 'zip' not in artifacts:
                target = Path(job['directory']) / 'prepared-frames.zip'
                if not target.exists():
                    temp = target.with_suffix('.zip.part')
                    with zipfile.ZipFile(temp, 'w', compression=zipfile.ZIP_STORED) as archive:
                        for path in frames:
                            archive.write(path, Path(path).name)
                    temp.replace(target)
                artifacts['zip'] = str(target)
            links = {}
            for key, label in LABELS.items():
                if key in artifacts:
                    relative = Path(artifacts[key]).relative_to(self.runs_root).as_posix()
                    links[label] = '/files/' + relative
            job.update(status='paused' if paused else 'done', stage='paused' if paused else 'done',
                       detail='파일 저장 후 중단했습니다. 저장된 구간부터 재개할 수 있습니다.' if paused else '요청한 구간의 파일 저장을 마쳤습니다.',
                       files=links, artifacts=artifacts, finished_at=time.time(), resumable=paused)
            job['timings_seconds'].update(result.get('pipeline_timings_seconds', {}))
            self.active = None
            self.collect_inputs(job)
            self.persist(job)

    def work(self, job):
        try:
            result = continue_pipeline(Path(job['directory']), job['spec'], self.cfg,
                                       lambda stage, detail: self.notify(job, stage, detail),
                                       should_stop=lambda: job.get('stop_requested', False))
            self.finish(job, result)
        except PipelinePaused as exc:
            self.finish(job, exc.result, paused=True)
        except (Exception, SystemExit) as exc:
            self.fail(job, str(exc))

    def resume(self, ident):
        with self.lock:
            if self.active:
                raise ValueError('실행 중인 작업이 있습니다.')
            job = self.jobs.get(ident)
            if not job or not job.get('resumable'):
                raise ValueError('입력이 저장된 중단 작업만 재개할 수 있습니다.')
            job.update(status='running', stage='queued', detail='저장된 파일부터 재개합니다.', resumable=False, stop_requested=False)
            job.pop('error', None)
            job.pop('finished_at', None)
            self.active = ident
            self.persist(job)
            threading.Thread(target=self.work, args=(job,), daemon=True).start()
            return self.state(ident)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    @property
    def control(self):
        return self.server.control

    def respond(self, status, data, mime='application/json; charset=utf-8'):
        encoded = json.dumps(data, ensure_ascii=False).encode('utf-8') if not isinstance(data, bytes) else data
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(encoded)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/':
            return self.respond(200, (APP_ROOT / 'index.html').read_bytes(), 'text/html; charset=utf-8')
        if parsed.path == '/setup':
            return self.respond(200, (APP_ROOT / 'SETUP.txt').read_bytes(), 'text/plain; charset=utf-8')
        if parsed.path == '/api/state':
            return self.respond(200, self.control.state(parse_qs(parsed.query).get('id', [None])[0]))
        if parsed.path.startswith('/files/'):
            root = self.control.runs_root.resolve()
            path = (root / unquote(parsed.path.removeprefix('/files/'))).resolve()
            if root not in path.parents or path.suffix.lower() not in ('.png', '.gif', '.webp', '.json', '.zip', '.mp4', '.jpg', '.jpeg', '.webm', '.mov') or not path.is_file():
                return self.respond(404, {'error': '파일을 찾을 수 없습니다.'})
            return self.respond(200, path.read_bytes(), mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
        return self.respond(404, {'error': '요청 경로가 없습니다.'})

    def do_POST(self):
        try:
            path = urlparse(self.path).path
            # Browser extension calls use their per-job token. GUI calls require same origin.
            if not path.startswith('/api/browser/'):
                if self.headers.get('Origin') not in (f'http://127.0.0.1:{PORT}', f'http://localhost:{PORT}'):
                    raise PermissionError('로컬 프로그램 화면에서 실행해 주세요.')
            size = int(self.headers.get('Content-Length', '0'))
            if path == '/api/upload':
                if self.headers.get_content_type() != 'multipart/form-data' or not 0 < size <= 268_435_456:
                    raise ValueError('업로드는 전체 256 MiB 이내 파일이어야 합니다.')
                return self.respond(200, self.control.upload(self.headers['Content-Type'], self.rfile.read(size)))
            if self.headers.get_content_type() != 'application/json':
                raise ValueError('JSON 요청만 받습니다.')
            limit = 49_000_000 if path == '/api/browser/result' else 50_000
            if not 0 < size <= limit:
                raise ValueError('요청 크기가 유효하지 않습니다.')
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError('요청 형식이 유효하지 않습니다.')
            if path == '/api/run':
                result = self.control.start(body)
            elif path == '/api/watch':
                result = self.control.set_watch(body)
            elif path == '/api/stop':
                result = self.control.stop()
            elif path == '/api/resume':
                result = self.control.resume(body.get('id'))
            elif path == '/api/browser/claim':
                result = self.control.claim(body)
            elif path == '/api/browser/event':
                result = self.control.event(body)
            elif path == '/api/browser/result':
                result = self.control.image_result(body)
            else:
                return self.respond(404, {'error': '요청 경로가 없습니다.'})
            self.respond(200, result)
        except PermissionError as exc:
            self.respond(403, {'error': str(exc)})
        except (ValueError, RuntimeError, SystemExit) as exc:
            self.respond(400, {'error': str(exc)})
        except Exception:
            self.respond(500, {'error': '프로그램 처리 오류입니다. 저장된 실행 폴더를 확인하세요.'})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--serve', action='store_true')
    parser.add_argument('--open', action='store_true')
    parser.add_argument('--process-video', type=Path, help='Existing video only; never generates media')
    parser.add_argument('--frames', type=int, default=16)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    cfg = configure()
    if args.process_video:
        if not args.out:
            parser.error('--process-video requires --out')
        args.out.mkdir(parents=True, exist_ok=False)
        result = continue_pipeline(args.out, {'frame_count': args.frames}, cfg,
                                   lambda stage, detail: print(json.dumps({'stage': stage, 'detail': detail}, ensure_ascii=False), flush=True),
                                   existing_clip=args.process_video.resolve())
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return
    control = Coordinator(cfg)
    try:
        server = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    except OSError:
        if args.open:
            from urllib.request import urlopen
            try:
                with urlopen(f'http://127.0.0.1:{PORT}/api/state', timeout=2) as response:
                    running = json.load(response)
                if running.get('connection') == 'ChatGPT 웹 · Grok 구독':
                    subprocess.Popen([cfg['chrome'], f'http://127.0.0.1:{PORT}/'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
            except (OSError, ValueError):
                pass
        raise
    server.control = control
    if args.open:
        subprocess.Popen([cfg['chrome'], f'http://127.0.0.1:{PORT}/'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f'Sprite Pipeline: http://127.0.0.1:{PORT}/', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    main()
