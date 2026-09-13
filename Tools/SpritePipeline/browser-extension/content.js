"use strict";

(() => {
  const HASH_PREFIX = "#sprite-pipeline=";
  const MAX_IMAGE_BYTES = 32 * 1024 * 1024;
  const COMPLETE_STABILITY_MS = 3000;
  let active = false;
  let stopped = false;
  let job = null;
  let observer = null;
  let interval = null;
  let scanning = false;
  let lastProgress = 0;
  let lastScan = 0;
  const candidates = new Map();
  const signatures = new Map();
  let badge = null;

  function show(message, failed = false) {
    if (!badge) {
      badge = document.createElement("div");
      badge.id = "sprite-pipeline-bridge-status";
      badge.setAttribute("role", "status");
      Object.assign(badge.style, {
        position: "fixed", bottom: "16px", left: "16px", zIndex: "2147483647",
        maxWidth: "460px", padding: "12px 16px", borderRadius: "8px",
        font: "14px/1.5 system-ui", color: "white", boxShadow: "0 2px 12px #0005",
        pointerEvents: "none"
      });
      document.documentElement.append(badge);
    }
    badge.style.background = failed ? "#792f34" : "#183e46";
    badge.textContent = `Sprite Pipeline: ${message}`;
  }

  async function send(type, fields = {}) {
    const result = await chrome.runtime.sendMessage({ type, ...fields });
    if (!result?.ok) throw new Error(result?.error ?? "브리지 응답이 없습니다.");
    return result;
  }

  function stop() {
    stopped = true;
    observer?.disconnect();
    if (interval) clearInterval(interval);
  }

  async function fail(error) {
    stop();
    const detail = error instanceof Error ? error.message : String(error);
    show(`${detail} 자동 재생성하지 않습니다.`, true);
    if (job) {
      await send("SP_FAIL", { detail }).catch(() => {
        show(`${detail} 로컬 서버 전달도 실패했습니다. 실행기 상태를 확인해 주세요.`, true);
      });
    }
  }

  function parseLaunch() {
    if (!location.hash.startsWith(HASH_PREFIX)) return null;
    if (!/^\/images\/?$/.test(location.pathname)) throw new Error("새 작업은 /images/에서만 시작할 수 있습니다.");
    const encoded = location.hash.slice(HASH_PREFIX.length);
    if (!/^[A-Za-z0-9_-]{1,2048}$/.test(encoded)) throw new Error("작업 링크 형식이 올바르지 않습니다.");
    const padded = encoded.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(encoded.length / 4) * 4, "=");
    const bytes = Uint8Array.from(atob(padded), (char) => char.charCodeAt(0));
    return JSON.parse(new TextDecoder().decode(bytes));
  }

  function generatedImages(ready = true) {
    // Narrow scope observed on the logged-in Korean Images page. No thumbnail-strip fallback.
    return [...document.querySelectorAll("main img")].filter((img) => {
      const alt = img.getAttribute("alt") ?? "";
      return (alt === "생성된 이미지" || alt.startsWith("생성된 이미지:")) &&
        img.closest('[id^="image-"]') && !!(img.currentSrc || img.src) &&
        (!ready || (img.complete && img.naturalWidth >= 256 && img.naturalHeight >= 256));
    });
  }

  async function signature(value) {
    if (!signatures.has(value)) {
      signatures.set(value, crypto.subtle.digest("SHA-256", new TextEncoder().encode(value)).then(
        (buffer) => [...new Uint8Array(buffer)].map((byte) => byte.toString(16).padStart(2, "0")).join("")
      ));
    }
    return signatures.get(value);
  }

  async function waitFor(test, timeout, errorMessage) {
    const deadline = Date.now() + timeout;
    while (Date.now() < deadline) {
      const value = test();
      if (value) return value;
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
    throw new Error(errorMessage);
  }

  async function submitOnce() {
    const input = await waitFor(
      () => document.querySelector('div#prompt-textarea[role="textbox"][contenteditable="true"]'),
      30000,
      "이미지 프롬프트 입력란을 찾지 못했습니다. 로그인·페이지·확장 선택자를 확인해야 합니다."
    );
    // Allow initial history images to finish loading before recording the baseline.
    await new Promise((resolve) => setTimeout(resolve, 1000));
    input.focus();
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(input);
    selection.removeAllRanges();
    selection.addRange(range);
    if (!document.execCommand("insertText", false, job.prompt)) {
      input.replaceChildren(document.createTextNode(job.prompt));
    }
    input.dispatchEvent(new InputEvent("input", {
      bubbles: true, inputType: "insertText", data: job.prompt
    }));

    const button = await waitFor(() => {
      const item = document.getElementById("composer-submit-button");
      return item && !item.disabled && item.getAttribute("aria-disabled") !== "true" ? item : null;
    }, 20000, "프롬프트 보내기 버튼이 준비되지 않았습니다. Enter 대체 제출은 하지 않습니다.");

    const baseline = await Promise.all([
      ...generatedImages(false).map((img) => signature(`src:${img.currentSrc || img.src}`)),
      ...[...document.querySelectorAll('main [id^="image-"]')].map((item) => signature(`container:${item.id}`))
    ]);
    const armed = await send("SP_ARM", { baseline });
    job = armed.job;
    if (!armed.armed) return;
    // Exactly one submission path. No Enter fallback and no automatic regeneration.
    button.click();
    await send("SP_EVENT", { stage: "submitted", detail: "ChatGPT 이미지 프롬프트를 한 번 제출했습니다." });
  }

  async function imagePayload(img) {
    const src = img.currentSrc || img.src;
    const url = new URL(src, location.href);
    if (url.origin !== "https://chatgpt.com" || !["https:", "blob:"].includes(url.protocol)) {
      throw new Error("관측 범위 밖 이미지 출처입니다. 출처를 검토하기 전 권한을 확대하지 않습니다.");
    }
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);
    let response;
    try {
      response = await fetch(url.href, {
        credentials: "same-origin", redirect: "error", signal: controller.signal
      });
      if (!response.ok) throw new Error(`이미지 다운로드 실패: HTTP ${response.status}`);
      const mime = (response.headers.get("content-type") ?? "").split(";")[0].trim();
      if (!["image/png", "image/jpeg", "image/webp"].includes(mime)) {
        throw new Error("PNG·JPEG·WebP 이미지 응답이 아닙니다.");
      }
      const declared = Number(response.headers.get("content-length"));
      if (declared > MAX_IMAGE_BYTES) throw new Error("이미지가 32 MiB를 초과했습니다.");
      const reader = response.body.getReader();
      const chunks = [];
      let size = 0;
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        size += value.length;
        if (size > MAX_IMAGE_BYTES) {
          await reader.cancel();
          throw new Error("이미지가 32 MiB를 초과했습니다.");
        }
        chunks.push(value);
      }
      if (!size) throw new Error("빈 이미지 응답입니다.");
      const bytes = new Uint8Array(size);
      let offset = 0;
      for (const chunk of chunks) {
        bytes.set(chunk, offset);
        offset += chunk.length;
      }
      const parts = [];
      for (let index = 0; index < bytes.length; index += 0x8000) {
        parts.push(String.fromCharCode(...bytes.subarray(index, index + 0x8000)));
      }
      return { mime, image_base64: btoa(parts.join("")) };
    } catch (error) {
      throw new Error(`이미지 파일 수신을 완료하지 못했습니다(CSP·CORS·네트워크 확인 필요): ${error.message}`);
    } finally {
      clearTimeout(timeout);
    }
  }

  async function scan() {
    if (stopped || scanning || Date.now() - lastScan < 900) return;
    scanning = true;
    lastScan = Date.now();
    try {
      if (Date.now() > job.deadline) throw new Error("이미지 완료 대기 15분을 초과했습니다.");
      const baseline = new Set(job.baseline);
      const found = [];
      for (const img of generatedImages()) {
        const id = await signature(`src:${img.currentSrc || img.src}`);
        const containerId = await signature(`container:${img.closest('[id^="image-"]').id}`);
        if (!baseline.has(id) && !baseline.has(containerId)) found.push({ img, id });
      }
      const current = new Set(found.map(({ id }) => id));
      for (const id of candidates.keys()) if (!current.has(id)) candidates.delete(id);
      for (const { img, id } of found) {
        const dimensions = `${img.naturalWidth}x${img.naturalHeight}`;
        const previous = candidates.get(id);
        if (!previous || previous.dimensions !== dimensions) {
          candidates.set(id, { dimensions, since: Date.now() });
          continue;
        }
        if (Date.now() - previous.since < COMPLETE_STABILITY_MS) continue;
        show("새 이미지 파일을 로컬 실행기로 전달하고 있습니다.");
        const payload = await imagePayload(img);
        await send("SP_RESULT", payload);
        stop();
        show("이미지 저장 완료. 다음 단계는 로컬 프로그램이 자동 실행합니다.");
        return;
      }
      if (Date.now() - lastProgress > 20000) {
        lastProgress = Date.now();
        await send("SP_EVENT", { stage: "progress", detail: "새 생성 이미지의 로드 완료를 기다리고 있습니다." });
      }
    } catch (error) {
      await fail(error);
    } finally {
      scanning = false;
    }
  }

  async function start() {
    if (active) return;
    active = true;
    try {
      const launch = parseLaunch();
      const connected = await send("SP_CONNECT", { job: launch });
      job = connected.job;
      // Ordinary ChatGPT tabs have no launch token or bound job: no DOM changes/network calls.
      if (!job) { active = false; return; }
      if (launch) history.replaceState(history.state, "", location.pathname + location.search);
      if (["completed", "failed", "result-uncertain"].includes(job.status)) {
        show(`이 작업은 ${job.status} 상태입니다. 재제출하지 않습니다.`, job.status !== "completed");
        return;
      }
      if (Date.now() > job.deadline) throw new Error("이전 작업의 대기 시간이 만료되었습니다.");
      show(job.submitted ? "이전 제출을 재개하여 결과만 기다립니다." : "이미지 프롬프트 입력을 준비하고 있습니다.");
      if (!job.submitted) await submitOnce();
      show("이미지 생성 대기 중입니다. 추가 추론·재제출은 하지 않습니다.");
      observer = new MutationObserver(() => { void scan(); });
      observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ["src", "alt"] });
      interval = setInterval(() => { void scan(); }, 1000);
      await scan();
    } catch (error) {
      await fail(error);
    }
  }

  window.addEventListener("hashchange", () => { if (!active) void start(); });
  void start();
})();
