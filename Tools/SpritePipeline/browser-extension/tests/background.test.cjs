"use strict";

// Offline protocol checks: no browser, generation request, or real network traffic.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname, "..", "background.js"), "utf8");
const credentials = { id: "job-1", token: "a".repeat(32), port: 8765 };
const sender = {
  tab: { id: 4 },
  url: "https://chatgpt.com/images/?signed=private#sprite-pipeline=private"
};

function harness() {
  const memory = {};
  const requests = [];
  let listener;
  let owner = null;
  let serverStatus = "ready";
  const chrome = {
    storage: { session: {
      async get(key) { return { [key]: structuredClone(memory[key]) }; },
      async set(values) { Object.assign(memory, structuredClone(values)); },
      async remove(key) { delete memory[key]; }
    } },
    runtime: { onMessage: { addListener(fn) { listener = fn; } } },
    tabs: { onRemoved: { addListener() {} } }
  };
  const fetch = async (url, options) => {
    const body = JSON.parse(options.body);
    const route = new URL(url).pathname.split("/").at(-1);
    requests.push({ route, body });
    assert.equal(Number.isInteger(body.tab_id), true, "Every POST must bind the actual sender tab");
    if (route === "claim" && owner === null) owner = body.tab_id;
    if (body.tab_id !== owner) return { ok: false, status: 409 };
    if (route === "event" && body.stage === "submitted") serverStatus = "submitted";
    if (route === "event" && body.stage === "failed") serverStatus = "failed";
    return {
      ok: true,
      json: async () => route === "claim" ? { prompt: "test image", status: serverStatus } : { ok: true }
    };
  };
  vm.runInNewContext(source, { chrome, fetch, URL, AbortController, setTimeout, clearTimeout }, {
    filename: "background.js"
  });
  const post = (type, fields = {}, from = sender) => new Promise((resolve) => {
    listener({ type, ...fields }, from, (result) => resolve(structuredClone(result)));
  });
  return { post, memory, requests };
}

async function main() {
  const test = harness();
  assert.equal((await test.post("SP_CONNECT", { job: credentials })).ok, true);
  assert.equal((await test.post("SP_CONNECT", { job: credentials })).ok, true);
  assert.equal(test.requests.filter((item) => item.route === "claim").length, 1);

  const baseline = ["b".repeat(64)];
  const reservations = await Promise.all([
    test.post("SP_ARM", { baseline }), test.post("SP_ARM", { baseline })
  ]);
  assert.deepEqual(reservations.map((item) => item.armed), [true, false]);
  await test.post("SP_EVENT", { stage: "submitted", detail: "submitted once" });
  const recovered = await test.post("SP_CONNECT", { job: credentials });
  assert.equal(recovered.job.submitted, true);
  assert.deepEqual(recovered.job.baseline, baseline);
  assert.equal(test.requests.filter((item) => item.route === "claim").length, 1);

  const otherTab = { ...sender, tab: { id: 5 } };
  assert.equal((await test.post("SP_CONNECT", { job: credentials }, otherTab)).ok, false);
  assert.equal((await test.post("SP_ARM", { baseline: [] }, otherTab)).ok, false);
  assert.equal(test.requests.filter((item) => item.route === "claim").at(-1).body.tab_id, 5);

  assert.equal((await test.post("SP_RESULT", { image_base64: "AA==", mime: "text/html" })).ok, false);
  assert.equal((await test.post("SP_RESULT", { image_base64: "AA==", mime: "image/png" })).ok, true);
  assert.equal((await test.post("SP_RESULT", { image_base64: "AA==", mime: "image/png" })).ok, false);
  const results = test.requests.filter((item) => item.route === "result");
  assert.equal(results.length, 1);
  assert.equal(results[0].body.tab_id, sender.tab.id);
  assert.equal(results[0].body.source_url, "https://chatgpt.com/images/");
  assert.equal((await test.post("SP_CONNECT", { job: credentials }, {
    tab: { id: 7 }, url: "https://example.com/"
  })).ok, false);
  assert.equal((await test.post("SP_CONNECT", { job: { ...credentials, port: 8080 } }, {
    ...sender, tab: { id: 8 }
  })).ok, false);

  const lost = harness();
  await lost.post("SP_CONNECT", { job: credentials });
  await lost.post("SP_ARM", { baseline });
  await lost.post("SP_EVENT", { stage: "submitted", detail: "submitted once" });
  delete lost.memory[`sprite-job:${sender.tab.id}`];
  const refused = await lost.post("SP_CONNECT", { job: credentials });
  assert.equal(refused.ok, true);
  assert.equal(refused.job.status, "failed");
  assert.equal(refused.job.submitted, true);
  assert.equal((await lost.post("SP_ARM", { baseline: [] })).ok, false);
  assert.equal(lost.requests.filter((item) => item.route === "event" && item.body.stage === "submitted").length, 1);
  assert.equal(lost.requests.filter((item) => item.route === "event" && item.body.stage === "failed").length, 1);
  assert.equal(lost.requests.at(-1).body.tab_id, sender.tab.id);
  assert.equal((await lost.post("SP_CONNECT", { job: credentials })).job.status, "failed");

  console.log("PASS: sender-tab binding on every POST; cross-tab refusal; lost submitted session refuses regeneration; retained session resumes; concurrent reservation; single result; MIME, origin and port guards.");
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
