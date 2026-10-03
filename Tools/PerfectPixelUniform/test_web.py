"""One hidden local-server integration case; no browser UI or external network."""
from __future__ import annotations
import base64
import hashlib
import io
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, ProxyHandler

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent


def main():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    process = subprocess.Popen([sys.executable, "-B", str(ROOT / "web.py"), "--port", str(port)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    opener = build_opener(ProxyHandler({}))
    url = "http://127.0.0.1:" + str(port)
    cases = []

    def request(path, payload=None, origin=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"} if data else {}
        if origin:
            headers["Origin"] = origin
        try:
            with opener.open(Request(url + path, data=data, headers=headers), timeout=10) as response:
                return response.status, response.read()
        except HTTPError as error:
            return error.code, error.read()

    try:
        deadline = time.monotonic() + 8
        while True:
            try:
                status, raw = request("/api/health")
                break
            except URLError:
                if time.monotonic() > deadline or process.poll() is not None:
                    raise RuntimeError("Local server startup failed")
                time.sleep(0.05)
        assert status == 200 and json.loads(raw)["application"] == "PerfectPixelUniform"
        cases.append("local server health")
        status, page = request("/")
        assert status == 200 and b"/api/normalize" in page and b"drawImage" not in page and b"<canvas" not in page
        cases.append("HTML served without canvas pre-resize")
        truth = np.random.default_rng(123).integers(1, 256, (32, 36, 3), dtype=np.uint8)
        source = np.repeat(np.repeat(truth, 4, axis=0), 4, axis=1)
        stream = io.BytesIO()
        Image.fromarray(source).save(stream, format="PNG")
        input_bytes = stream.getvalue()
        payload = {"filename": "known-native-x4.png", "image_base64": base64.b64encode(input_bytes).decode("ascii")}
        start = time.perf_counter()
        status, raw = request("/api/normalize", payload, url)
        elapsed = time.perf_counter() - start
        assert status == 200, raw.decode()
        answer = json.loads(raw)
        status, png = request(answer["output_url"])
        assert status == 200 and np.array_equal(np.asarray(Image.open(io.BytesIO(png))), truth)
        cases.append("HTTP auto normalization recovers independently known RGB image; PNG not preview-scaled")
        status, saved_source = request(answer["source_url"])
        assert status == 200 and saved_source == input_bytes
        status, receipt_bytes = request(answer["receipt_url"])
        receipt = json.loads(receipt_bytes)
        assert status == 200 and receipt["_web"]["source_sha256"] == hashlib.sha256(input_bytes).hexdigest()
        assert receipt["_web"]["output_sha256"] == hashlib.sha256(png).hexdigest()
        cases.append("exact uploaded bytes and output SHA persisted; receipt retrievable")
        status, _ = request("/api/normalize", payload, "https://external.invalid")
        assert status == 403
        cases.append("external Origin rejected before processing")
        blank_stream = io.BytesIO()
        Image.new("RGB", (64, 64), (120, 120, 120)).save(blank_stream, format="PNG")
        status, failure_bytes = request("/api/normalize", {"filename": "blank.png", "image_base64": base64.b64encode(blank_stream.getvalue()).decode("ascii")}, url)
        assert status == 422
        failure = json.loads(failure_bytes)
        assert failure["error_type"] == "GridDetectionError"
        status, _ = request(failure["failure_url"])
        assert status == 200
        cases.append("blank detection failure displayed and preserved, no replacement output")
        report = {"schema": "perfect-pixel-uniform-web-tests/1", "passed": True, "cases": cases,
                  "processing_http_seconds": elapsed, "core_seconds": answer["report"]["elapsed_seconds"],
                  "successful_run_id": answer["run_id"], "failed_run_id": failure["run_id"],
                  "scope": "HTTP/PNG/HTML integration; no personal browser UI automation or Unity changes"}
        destination = Path(sys.argv[1])
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(json.dumps(report, ensure_ascii=False))
    finally:
        process.terminate()
        process.communicate(timeout=5)


if __name__ == "__main__":
    main()
