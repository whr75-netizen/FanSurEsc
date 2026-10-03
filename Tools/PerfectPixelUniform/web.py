"""Local browser wrapper for the separate uniform-grid normalization path."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import io
import json
import mimetypes
import re
import socket
import threading
import uuid
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

import numpy as np
from PIL import Image

from uniform import process_array
from cleanup import process_cleanup


ROOT = Path(__file__).resolve().parent
def code_sha():
    return hashlib.sha256(b"".join((ROOT / name).read_bytes() for name in ("uniform.py", "cleanup.py", "web.py"))).hexdigest()


CORE_SHA = code_sha()
RUNS = ROOT / "runs"
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_PIXELS = 4_000_000
MAX_REQUEST_BYTES = ((MAX_FILE_BYTES + 2) // 3) * 4 + 32_768
WORK_LOCK = threading.Lock()
RUN_ID = re.compile(r"^\d{8}T\d{12}Z-[0-9a-f]{32}$")
FORMAT_SUFFIXES = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp", "BMP": ".bmp", "TIFF": ".tiff"}


def json_default(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError("Not JSON serializable: " + type(value).__name__)


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=json_default).encode("utf-8")


def save_new(path, content):
    with path.open("xb") as stream:
        stream.write(content)


class LocalServer(ThreadingHTTPServer):
    # Windows SO_REUSEADDR can allow two listeners and send requests to old code.
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class Handler(BaseHTTPRequestHandler):
    server_version = "PerfectPixelUniform/3"

    def reply(self, status, body, content_type="application/json; charset=utf-8"):
        payload = json_bytes(body) if not isinstance(body, bytes) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' blob:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(payload)

    def local_request(self):
        port = self.server.server_port
        allowed_hosts = {"127.0.0.1:" + str(port), "localhost:" + str(port)}
        allowed_origins = {"http://" + host for host in allowed_hosts}
        host = self.headers.get("Host", "").lower()
        origin = self.headers.get("Origin")
        if host not in allowed_hosts or (origin is not None and origin not in allowed_origins):
            self.reply(403, {"error": "외부 Host 또는 Origin 요청은 허용하지 않습니다."})
            return False
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            self.reply(403, {"error": "외부 사이트 요청은 허용하지 않습니다."})
            return False
        return True

    def do_GET(self):
        if not self.local_request():
            return
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            self.reply(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
            return
        if path == "/api/health":
            self.reply(200, {"application": "PerfectPixelUniform", "version": 3, "busy": WORK_LOCK.locked(), "loaded_core_sha256": CORE_SHA})
            return
        parts = path.split("/")
        if len(parts) != 4 or parts[1] != "runs" or not RUN_ID.fullmatch(parts[2]):
            self.reply(404, {"error": "경로가 없습니다."})
            return
        name = parts[3]
        if name not in {"output.png", "receipt.json", "failure.json", "source.bin"} and name not in {"source" + suffix for suffix in FORMAT_SUFFIXES.values()}:
            self.reply(404, {"error": "경로가 없습니다."})
            return
        artifact = RUNS / parts[2] / name
        if not artifact.is_file():
            self.reply(404, {"error": "파일이 없습니다."})
            return
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        self.reply(200, artifact.read_bytes(), content_type)

    def do_POST(self):
        if not self.local_request():
            return
        if self.path != "/api/normalize":
            self.reply(404, {"error": "경로가 없습니다."})
            return
        if code_sha() != CORE_SHA:
            self.reply(503, {"error": "계산 코드가 변경되었습니다. 실행기를 재시작한 뒤 처리해 주세요."})
            return
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            self.reply(415, {"error": "application/json 요청만 허용합니다."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.reply(400, {"error": "Content-Length가 올바르지 않습니다."})
            return
        if length <= 0 or length > MAX_REQUEST_BYTES or self.headers.get("Transfer-Encoding"):
            self.reply(413, {"error": "요청 제한은 이미지 20 MiB입니다."})
            return
        if not WORK_LOCK.acquire(blocking=False):
            self.reply(409, {"error": "이미 처리 중입니다. 현재 작업이 끝난 뒤 실행해 주세요."})
            return
        run_dir = None
        source_name = "source.bin"
        try:
            request = json.loads(self.rfile.read(length))
            encoded = request.get("image_base64")
            if not isinstance(encoded, str):
                raise ValueError("image_base64 문자열이 필요합니다.")
            if encoded.startswith("data:"):
                header, encoded = encoded.split(",", 1)
                if not header.endswith(";base64"):
                    raise ValueError("base64 이미지 데이터만 허용합니다.")
            try:
                raw = base64.b64decode(encoded, validate=True)
            except (binascii.Error, ValueError) as error:
                raise ValueError("이미지 base64 데이터가 올바르지 않습니다.") from error
            if not raw or len(raw) > MAX_FILE_BYTES:
                raise ValueError("이미지 제한은 20 MiB입니다.")
            run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid.uuid4().hex
            RUNS.mkdir(exist_ok=True)
            run_dir = RUNS / run_id
            run_dir.mkdir(exist_ok=False)
            # Store the exact uploaded bytes even if decoding or normalization fails.
            save_new(run_dir / "source.bin", raw)
            with Image.open(io.BytesIO(raw)) as source:
                if source.mode not in ("RGB", "RGBA"):
                    raise ValueError("입력은 RGB/RGBA uint8만 지원합니다. 자동 모드 변환은 하지 않습니다: " + source.mode)
                if source.width * source.height > MAX_PIXELS:
                    raise ValueError("입력 제한은 4,000,000 pixels입니다.")
                if getattr(source, "n_frames", 1) != 1:
                    raise ValueError("단일 정지 이미지만 지원합니다.")
                source.load()
                pixels = np.array(source, copy=True)
                source_mode = source.mode
                suffix = FORMAT_SUFFIXES.get(source.format, ".bin")
            if pixels.dtype != np.uint8:
                raise ValueError("입력 배열은 uint8이어야 합니다.")
            source_name = "source" + suffix
            if source_name != "source.bin":
                save_new(run_dir / source_name, raw)
            mode = request.get("mode", "lossless")  # Preserve existing V2 API calls.
            if mode == "cleanup":
                output, report = process_cleanup(pixels, request.get("strength", 4), request.get("palette_colors", 256))
            elif mode == "lossless":
                output, report = process_array(pixels)
            else:
                raise ValueError("처리 모드는 cleanup 또는 lossless여야 합니다.")
            if not isinstance(output, np.ndarray) or output.dtype != np.uint8 or output.ndim != 3:
                raise ValueError("처리기가 uint8 RGB/RGBA 배열을 반환하지 않았습니다.")
            if output.shape[2] != pixels.shape[2] or output.shape[0] <= 0 or output.shape[1] <= 0:
                raise ValueError("출력 모드가 입력과 다르거나 크기가 올바르지 않습니다.")
            png_stream = io.BytesIO()
            result_image = Image.fromarray(output)
            if result_image.mode != source_mode:
                raise ValueError("입출력 이미지 모드가 다릅니다.")
            result_image.save(png_stream, format="PNG")
            png = png_stream.getvalue()
            receipt = dict(report)
            receipt["_web"] = {
                "schema": "perfect-pixel-uniform-local-web/1",
                "source_filename": str(request.get("filename", ""))[:256],
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "output_sha256": hashlib.sha256(png).hexdigest(),
                "input_mode": source_mode,
                "output_mode": result_image.mode,
                "input_bytes_preserved": True,
                "preview_scaling_only": True,
                "run_id": run_id,
                "processing_mode": mode,
            }
            receipt_data = json_bytes(receipt)
            save_new(run_dir / "output.png", png)
            save_new(run_dir / "receipt.json", receipt_data)
            prefix = "/runs/" + run_id + "/"
            self.reply(200, {
                "run_id": run_id,
                "source_url": prefix + source_name,
                "output_url": prefix + "output.png",
                "receipt_url": prefix + "receipt.json",
                "report": report,
                "input_mode": source_mode,
                "output_mode": result_image.mode,
            })
        except Exception as error:
            failure = {"error": str(error), "error_type": type(error).__name__}
            if isinstance(getattr(error, "report", None), dict):
                failure["report"] = error.report
            if run_dir is not None:
                failure["run_id"] = run_dir.name
                failure["failure_url"] = "/runs/" + run_dir.name + "/failure.json"
                failure["source_url"] = "/runs/" + run_dir.name + "/" + source_name
                save_new(run_dir / "failure.json", json_bytes(failure))
            self.reply(422, failure)
        finally:
            WORK_LOCK.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--open", action="store_true", help="기본 브라우저로 새 로컬 페이지를 엽니다.")
    parser.add_argument("--port", type=int, default=8768)
    args = parser.parse_args()
    url = "http://127.0.0.1:" + str(args.port)
    try:
        server = LocalServer(("127.0.0.1", args.port), Handler)
    except OSError:
        # Opening an already-running instance must not create another worker.
        try:
            opener = build_opener(ProxyHandler({}))
            with opener.open(url + "/api/health", timeout=2) as response:
                health = json.load(response)
            if health.get("application") != "PerfectPixelUniform":
                raise RuntimeError("다른 프로그램이 로컬 포트를 사용 중입니다.")
            if health.get("version") != 3 or health.get("loaded_core_sha256") != CORE_SHA:
                raise RuntimeError("이전 버전 실행기가 동작 중입니다. 해당 실행기를 종료하고 다시 실행해 주세요.")
        except (URLError, ValueError, RuntimeError):
            raise
        if args.open:
            webbrowser.open(url, new=2)
        return
    server.daemon_threads = True
    if args.open:
        threading.Timer(0.2, lambda: webbrowser.open(url, new=2)).start()
    print("PerfectPixel Uniform: " + url, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
