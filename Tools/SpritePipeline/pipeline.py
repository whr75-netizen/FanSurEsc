"""Sequential pipeline. The browser delivers an image; no LLM schedules steps."""
from __future__ import annotations

import base64
from io import BytesIO
import json
import os
from pathlib import Path
import time
import zipfile

from runtime import configure

IMAGE_CONSTRAINTS = '''
제작 입력 조건: 이미지 한 장에 캐릭터 한 명의 전신을 중앙에 배치하세요.
머리부터 발끝까지 모두 보이고 사방에 충분한 여백이 있어야 합니다.
정방형 1024×1024, 배경은 균일한 초록색 #00FF00입니다.
문자, 설명판, 분할 화면, 여러 포즈 시트 없이 단일 원화 한 장만 생성하세요.
캐릭터 디자인과 그림체는 위 사용자 프롬프트를 따르세요.
'''
VIDEO_CONSTRAINTS = '''
제작 입력 조건: 제공된 캐릭터의 외형을 유지하세요. 고정 카메라, 제자리 동작,
단색 초록 배경 유지, 한 동작 주기가 자연스럽게 반복되는 영상입니다.
몸 전체를 프레임 안에 유지하고 불필요하게 큰 머리카락 움직임은 줄이세요.
카메라 줌/이동, 화면 전환, 새 인물, 자막은 넣지 마세요.
'''


def atomic_json(path: Path, value: dict) -> None:
    tmp = path.with_name(path.name + '.part')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, path)


def validate_request(value: dict, *, require_gpt=None, require_grok=None) -> dict:
    mode = value.get('mode', 'all')
    if mode not in ('all', 'image', 'video', 'frames', 'pixel'):
        raise ValueError('지원하지 않는 실행 단계입니다.')
    result = {'mode': mode}
    required = {
        'gpt_prompt': mode in ('all', 'image') if require_gpt is None else require_gpt,
        'grok_prompt': mode in ('all', 'video') if require_grok is None else require_grok,
    }
    for key in ('gpt_prompt', 'grok_prompt'):
        text = value.get(key, '')
        if not isinstance(text, str) or len(text) > 12000 or (required[key] and not text.strip()):
            raise ValueError('이번 생성 단계에 필요한 프롬프트를 1–12000자로 입력하세요.')
        result[key] = text.strip()
    count = value.get('frame_count')
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 16:
        raise ValueError('프레임 수는 1–16 사이의 정수여야 합니다.')
    result['frame_count'] = count
    return result


def image_prompt(spec: dict) -> str:
    return spec['gpt_prompt'] + '\n\n' + IMAGE_CONSTRAINTS


def subscription_credential():
    from sprite_gen.gen.xai import resolve_credential, AUTH_SOURCE_GROK_LOGIN
    credential = resolve_credential()
    if credential.source != AUTH_SOURCE_GROK_LOGIN:
        raise RuntimeError('Grok 구독 로그인이 필요합니다. 별도 과금 API 키로 전환하지 않습니다. grok login을 확인하세요.')
    return credential


def save_browser_image(encoded: str, dest: Path) -> None:
    """Decode one returned artifact; never inspect its artistic quality."""
    from PIL import Image
    if not isinstance(encoded, str) or not encoded or len(encoded) > 48_000_000:
        raise ValueError('브라우저 이미지 데이터 크기가 유효하지 않습니다.')
    data = base64.b64decode(encoded, validate=True)
    with Image.open(BytesIO(data)) as im:
        if im.width < 256 or im.height < 256 or im.width * im.height > 16_777_216:
            raise ValueError('생성 이미지 크기가 유효하지 않습니다.')
        im.load()
        if dest.exists():
            raise ValueError('이 작업의 이미지가 이미 저장됐습니다. 중복 결과를 받지 않습니다.')
        temp = dest.with_name(dest.name + '.part')
        im.save(temp, format='PNG')
    os.replace(temp, dest)


class PipelinePaused(RuntimeError):
    def __init__(self, stage: str, result: dict):
        super().__init__(f'{stage} 단계까지 저장하고 중단했습니다.')
        self.stage = stage
        self.result = result


def continue_pipeline(run_dir: Path, spec: dict, cfg: dict, notify, *,
                      existing_clip: Path | None = None, should_stop=None) -> dict:
    mode = spec.get('mode', 'all')
    started = time.perf_counter()
    timing_path = run_dir / 'stage-times.json'
    timings = json.loads(timing_path.read_text(encoding='utf-8')) if timing_path.exists() else {}
    result_path = run_dir / 'result.json'

    def read(path: Path):
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None

    def stamp(result: dict) -> dict:
        return {**result, 'mode': mode, 'pipeline_timings_seconds': dict(timings),
                'local_continuation_seconds': round(time.perf_counter() - started, 3)}

    def stop_after(stage: str, result: dict):
        if should_stop is not None and should_stop():
            raise PipelinePaused(stage, stamp(result))

    def checkpoint(stage: str, result: dict) -> dict:
        atomic_json(run_dir / f'{stage}-result.json', result)
        stop_after(stage, result)
        return result

    def finish(result: dict) -> dict:
        result = stamp(result)
        atomic_json(result_path, result)
        stop_after(mode, result)
        return result

    def done(stage: str, begin: float):
        timings[stage] = round(time.perf_counter() - begin, 3)
        atomic_json(timing_path, timings)

    completed = read(result_path)
    if completed is not None and completed.get('mode', 'all') == mode:
        return completed
    image = run_dir / 'source.png'
    existing_files = {}
    for key, path in (('image', image), ('video', run_dir / 'clip.mp4')):
        if path.is_file():
            existing_files[key] = str(path)
    stop_after('현재', {'files': existing_files})
    if mode == 'image':
        if not image.is_file():
            raise RuntimeError('GPT 이미지 저장 완료를 기다리고 있습니다.')
        return finish({'files': {'image': str(image)}})

    cfg = configure(cfg)
    clip = Path(existing_clip) if existing_clip is not None else run_dir / 'clip.mp4'
    prepared_input = spec.get('prepared_input')
    prepared = read(run_dir / 'frames-result.json')
    needs_video = mode == 'video' or (mode == 'all' and not prepared_input and prepared is None)
    if needs_video and not clip.is_file():
        from PIL import Image
        from sprite_gen.video.canvas import pad_canvas, profile_for
        from sprite_gen.gen.video import VideoRequest, generate_video
        from sprite_gen.gen.xai import http_json
        canvas = run_dir / 'canvas.png'
        if not image.is_file():
            raise RuntimeError('GPT 이미지 저장 완료를 기다리고 있습니다.')
        if not canvas.is_file():
            notify('canvas', '단색 배경·공통 캔버스를 준비합니다.')
            begin = time.perf_counter()
            with Image.open(image) as source:
                canvas_image, info = pad_canvas(source, profile_for(None, 'square'), key='green')
                temp = canvas.with_name('canvas.png.part')
                canvas_image.save(temp, format='PNG')
            os.replace(temp, canvas)
            atomic_json(run_dir / 'canvas.json', info)
            done('canvas', begin)
        checkpoint('canvas', {'files': {'image': str(image), 'canvas': str(canvas)}})
        if not clip.is_file():
            notify('video', 'Grok 구독으로 영상 1개를 생성합니다. 완료 대기는 코드가 처리합니다.')
            credential = subscription_credential()
            journal = run_dir / 'video-request.json'
            saved = json.loads(journal.read_text(encoding='utf-8')) if journal.exists() else {}
            if saved.get('submitted') and not saved.get('request_id'):
                raise RuntimeError('이전 영상 요청의 응답을 확인하지 못했습니다. 중복 생성을 막기 위해 자동 재전송하지 않습니다.')

            def transport(method, url, token, body):
                if method == 'POST':
                    if saved.get('request_id'):
                        return 202, {'request_id': saved['request_id']}
                    atomic_json(journal, {'submitted': True})
                code, response = http_json(method, url, token, body)
                if method == 'POST' and isinstance(response, dict) and response.get('request_id'):
                    atomic_json(journal, {'submitted': True, 'request_id': response['request_id']})
                return code, response

            begin = time.perf_counter()
            result = generate_video(VideoRequest(
                image=canvas, prompt=spec['grok_prompt'] + '\n\n' + VIDEO_CONSTRAINTS,
                out=clip, duration=int(cfg['video_duration']), resolution='720p',
                model=cfg['video_model'], generate_audio=False,
            ), credential=credential, call=transport)
            atomic_json(run_dir / 'video-report.json', result.to_dict())
            done('video', begin)
    if needs_video:
        if not clip.is_file():
            raise RuntimeError('사용할 영상 파일이 없습니다.')
        video_result = checkpoint('video', {'files': {'video': str(clip)}})
        if mode == 'video':
            return finish(video_result)

    from postprocess import prepare_frames, pixel_frames

    def unused_path(prefix: str, suffix: str = '') -> Path:
        attempt = 1
        while (run_dir / f'{prefix}-{attempt}{suffix}').exists():
            attempt += 1
        return run_dir / f'{prefix}-{attempt}{suffix}'

    if prepared is None:
        if prepared_input:
            prepared = prepared_input
        elif mode == 'pixel':
            raise RuntimeError('픽셀화할 프레임 목록이나 manifest가 필요합니다.')
        else:
            if not clip.is_file():
                raise RuntimeError('프레임을 추출할 영상 파일이 없습니다.')
            notify('frames', '선택된 프레임만 추출하고 배경을 제거합니다.')
            begin = time.perf_counter()
            prepared = prepare_frames(
                clip, unused_path('prepared'), spec['frame_count'],
                ffmpeg=Path(cfg['ffmpeg']), ffprobe=Path(cfg['ffprobe']),
                key='green', workers=int(cfg['workers']), on_progress=notify,
            )
            prepared['files']['prepared'] = prepared['files']['manifest']
            done('frames', begin)
            checkpoint('frames', prepared)
    if isinstance(prepared, dict) and prepared.get('files', {}).get('manifest'):
        prepared['files']['prepared'] = prepared['files']['manifest']
    if mode == 'frames':
        return finish(prepared)
    stop_after('frames', prepared if isinstance(prepared, dict) else {'files': {'keyed_frames' if isinstance(prepared, list) else 'prepared': prepared}})

    result = read(run_dir / 'pixel-result.json')
    if result is None:
        export = unused_path('export')
        notify('pixel', '준비된 프레임을 PerfectPixel로 처리합니다.')
        begin = time.perf_counter()
        result = pixel_frames(
            prepared, export, img2webp=Path(cfg['img2webp']),
            engine_root=Path(cfg['engine_root']), duration=spec.get('duration', 1.0), workers=int(cfg['workers']), on_progress=notify,
        )
        result['export_dir'] = str(export)
        done('pixel', begin)
        checkpoint('pixel', result)
    else:
        stop_after('pixel', result)
    export = Path(result['export_dir'])
    archive = unused_path('animation', '.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_STORED) as z:
        for name, value in result['files'].items():
            for item in value if isinstance(value, list) else [value]:
                path = Path(item)
                z.write(path, path.relative_to(export))
    result['files']['zip'] = str(archive)
    return finish(result)
