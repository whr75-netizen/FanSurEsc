"use strict";

const PORT = 8765;
const MAX_IMAGE_BYTES = 32 * 1024 * 1024;
const JOB_TIMEOUT_MS = 15 * 60 * 1000;
const queues = new Map();
const terminal = new Set(["completed", "failed", "result-uncertain"]);
const keyFor = (tabId) => `sprite-job:${tabId}`;

function checkSender(sender) {
  if (!Number.isInteger(sender.tab?.id) || new URL(sender.url).origin !== "https://chatgpt.com") {
    throw new Error("ChatGPT 탭에서 시작한 요청만 허용됩니다.");
  }
  return sender.tab.id;
}

function checkCredentials(job) {
  if (!job || !/^[A-Za-z0-9_-]{1,128}$/.test(job.id) ||
      !/^[A-Za-z0-9_-]{24,128}$/.test(job.token) || job.port !== PORT) {
    throw new Error("작업 ID·토큰·로컬 포트가 올바르지 않습니다.");
  }
  return { id: job.id, token: job.token, port: PORT };
}

async function readJob(tabId) {
  return (await chrome.storage.session.get(keyFor(tabId)))[keyFor(tabId)] ?? null;
}

async function saveJob(tabId, job) {
  await chrome.storage.session.set({ [keyFor(tabId)]: job });
}

async function localPost(job, route, fields = {}, timeout = 15000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(`http://127.0.0.1:${PORT}/api/browser/${route}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...fields, id: job.id, token: job.token, tab_id: job.tab_id }),
      credentials: "omit",
      redirect: "error",
      signal: controller.signal
    });
    if (!response.ok) throw new Error(`로컬 서버 ${route} 응답: HTTP ${response.status}`);
    return await response.json();
  } finally {
    clearTimeout(timer);
  }
}

async function failJob(tabId, job, detail) {
  job.status = "failed";
  job.detail = String(detail).slice(0, 1500);
  await saveJob(tabId, job);
  await localPost(job, "event", { stage: "failed", detail: job.detail });
  return job;
}

async function handle(message, sender) {
  const tabId = checkSender(sender);
  let job = await readJob(tabId);

  if (message.type === "SP_CONNECT") {
    if (!message.job) return { job };
    const credentials = { ...checkCredentials(message.job), tab_id: tabId };
    if (job && job.id === credentials.id && job.token === credentials.token) return { job };
    if (job && !terminal.has(job.status)) throw new Error("이 탭에는 이미 진행 중인 작업이 있습니다.");
    // A launcher must open a distinct tab for each job. Bind it before any submission.
    const claimed = await localPost(credentials, "claim");
    if (typeof claimed.prompt !== "string" || !claimed.prompt.trim()) {
      throw new Error("서버가 유효한 이미지 프롬프트를 반환하지 않았습니다.");
    }
    if (terminal.has(claimed.status)) throw new Error("이미 종료된 작업은 다시 제출하지 않습니다.");
    if (claimed.status === "submitted") {
      // Server remembers submission, but this tab lost its baseline. Never create again.
      job = {
        ...credentials,
        prompt: "",
        submitted: true,
        baseline: [],
        deadline: Date.now()
      };
      await failJob(tabId, job, "이미 제출된 작업의 브라우저 세션·이미지 기준 목록이 없습니다. 중복 생성을 막기 위해 중단합니다.");
      return { job };
    }
    job = {
      ...credentials,
      prompt: claimed.prompt,
      status: "preparing",
      submitted: false,
      baseline: [],
      deadline: Date.now() + JOB_TIMEOUT_MS
    };
    await saveJob(tabId, job);
    return { job };
  }

  if (!job) throw new Error("이 탭에 연결된 작업이 없습니다.");
  if (message.type === "SP_STATUS") return { job };
  if (terminal.has(job.status)) throw new Error(`종료된 작업입니다: ${job.status}`);

  if (message.type === "SP_ARM") {
    if (job.submitted) return { armed: false, job };
    if (!Array.isArray(message.baseline) || message.baseline.length > 1000 ||
        message.baseline.some((item) => !/^[a-f0-9]{64}$/.test(item))) {
      throw new Error("이미지 기준 목록이 올바르지 않습니다.");
    }
    // Persist BEFORE the click: interrupted navigation may stop this job, never duplicate it.
    job.submitted = true;
    job.status = "armed";
    job.baseline = message.baseline;
    job.submittedAt = Date.now();
    job.deadline = Date.now() + JOB_TIMEOUT_MS;
    await saveJob(tabId, job);
    await localPost(job, "event", { stage: "submitted", detail: "이미지 제출을 예약했습니다. 중복 제출하지 않습니다." });
    return { armed: true, job };
  }

  if (message.type === "SP_EVENT") {
    if (!job.submitted || !["submitted", "progress"].includes(message.stage)) {
      throw new Error("작업 단계가 올바르지 않습니다.");
    }
    job.status = message.stage;
    job.detail = String(message.detail ?? "").slice(0, 1500);
    await saveJob(tabId, job);
    await localPost(job, "event", { stage: message.stage, detail: job.detail });
    return { job };
  }

  if (message.type === "SP_FAIL") {
    return { job: await failJob(tabId, job, message.detail) };
  }

  if (message.type === "SP_RESULT") {
    if (!job.submitted || typeof message.image_base64 !== "string" ||
        message.image_base64.length > Math.ceil(MAX_IMAGE_BYTES / 3) * 4 ||
        !/^[A-Za-z0-9+/]+={0,2}$/.test(message.image_base64) ||
        !["image/png", "image/jpeg", "image/webp"].includes(message.mime)) {
      throw new Error("결과 이미지 데이터가 올바르지 않거나 32 MiB를 초과했습니다.");
    }
    // Never forward a signed asset URL or fragment token into the server's provenance.
    const page = new URL(sender.url);
    const source_url = `${page.origin}${page.pathname}`;
    job.status = "result-uncertain";
    await saveJob(tabId, job);
    await localPost(job, "result", {
      image_base64: message.image_base64,
      mime: message.mime,
      source_url
    }, 30000);
    job.status = "completed";
    job.prompt = "";
    job.baseline = [];
    await saveJob(tabId, job);
    return { job };
  }

  throw new Error("지원하지 않는 브리지 명령입니다.");
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (typeof message?.type !== "string" || !message.type.startsWith("SP_")) return false;
  const tabId = sender.tab?.id;
  const previous = queues.get(tabId) ?? Promise.resolve();
  const current = previous.catch(() => {}).then(() => handle(message, sender));
  queues.set(tabId, current);
  current.then(
    (result) => sendResponse({ ok: true, ...result }),
    (error) => sendResponse({ ok: false, error: error.message })
  ).finally(() => {
    if (queues.get(tabId) === current) queues.delete(tabId);
  });
  return true;
});

chrome.tabs.onRemoved.addListener((tabId) => {
  const previous = queues.get(tabId) ?? Promise.resolve();
  const current = previous.catch(() => {}).then(async () => {
    const job = await readJob(tabId);
    if (job && !terminal.has(job.status)) {
      await failJob(tabId, job, "ChatGPT 작업 탭이 닫혔습니다. 자동 재제출하지 않습니다.").catch(() => {});
    }
    await chrome.storage.session.remove(keyFor(tabId));
  });
  queues.set(tabId, current);
  current.finally(() => {
    if (queues.get(tabId) === current) queues.delete(tabId);
  }).catch(() => {});
});
