// SPDX-License-Identifier: MPL-2.0
import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
const value = key => args[args.indexOf(key) + 1];
const browser = value("--browser");
const mode = args.includes("--mode") ? value("--mode") : "candidate";
const output = path.resolve(root, args.includes("--output") ? value("--output") : "out/performance-settings.json");
if (!args.includes("--browser") || !["baseline", "candidate", "both"].includes(mode) ||
    !output.startsWith(path.join(root, "out") + path.sep)) {
  throw new Error("Use --browser <Chromium executable> --mode baseline|candidate|both --output out/result.json");
}
await fs.mkdir(path.join(root, "out"), { recursive: true });
if (mode !== "candidate") {
  let source;
  if (args.includes("--baseline-ref")) {
    const ref = value("--baseline-ref");
    if (!/^[a-f0-9]{7,40}$/.test(ref)) throw new Error("Baseline must be an exact Git commit");
    const result = spawnSync("git", ["show", `${ref}:browser/settings.js`], { cwd: root, encoding: "utf8", windowsHide: true });
    if (result.status) throw new Error(result.stderr);
    source = result.stdout;
  } else {
    source = await fs.readFile(path.join(root, "browser/settings.js"), "utf8");
  }
  await fs.writeFile(path.join(root, "out/performance-baseline-settings.js"), source);
}
const profile = await fs.mkdtemp(path.join(root, "out/performance-profile-"));
const child = spawn(browser, ["--headless=new", "--remote-debugging-port=0", `--user-data-dir=${profile}`,
  "--no-first-run", "--no-default-browser-check", "--disable-background-networking", "--disable-extensions",
  "--disable-sync", "--metrics-recording-only", "--allow-file-access-from-files", "about:blank"],
  { stdio: "ignore", windowsHide: true });
let startupError;
child.on("error", error => { startupError = error; });
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
let socket;
const pending = new Map();
let nextId = 0;
function command(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++nextId;
    const timeout = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, 20000);
    pending.set(id, { resolve, reject, timeout });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
try {
  let port;
  for (let attempt = 0; attempt < 300; attempt++) {
    if (startupError) throw startupError;
    try {
      port = (await fs.readFile(path.join(profile, "DevToolsActivePort"), "utf8")).split("\n")[0];
      break;
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
      await delay(100);
    }
  }
  if (!port) throw new Error("Headless browser did not expose its debugging port");
  const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const target = targets.find(entry => entry.type === "page");
  if (!target) throw new Error("No benchmark browser page");
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { socket.addEventListener("open", resolve, { once: true }); socket.addEventListener("error", reject, { once: true }); });
  let pageError;
  socket.addEventListener("message", event => {
    const response = JSON.parse(event.data);
    if (response.method === "Runtime.exceptionThrown") pageError = response.params.exceptionDetails.exception?.description;
    const request = pending.get(response.id);
    if (request) {
      clearTimeout(request.timeout); pending.delete(response.id);
      if (response.error) request.reject(new Error(JSON.stringify(response.error)));
      else request.resolve(response.result);
    }
  });
  await command("Runtime.enable");
  await command("Page.navigate", { url: pathToFileURL(path.join(root, "benchmarks/settings-ui.html")).href + `?mode=${mode}` });
  let report;
  for (let attempt = 0; attempt < 600; attempt++) {
    const result = await command("Runtime.evaluate", { expression: "document.getElementById('results')?.textContent", returnByValue: true });
    const text = result.result.value;
    if (text?.startsWith("{")) { report = JSON.parse(text); break; }
    if (pageError) throw new Error(pageError);
    await delay(100);
  }
  if (!report || report.error) throw new Error(report?.error ?? "Benchmark did not finish");
  report.source_hashes = {};
  for (const name of ["browser/settings.js", "browser/settings-model.mjs", "config/customization.json", ...(mode === "candidate" ? [] : ["out/performance-baseline-settings.js"])]) {
    report.source_hashes[name] = createHash("sha256").update(await fs.readFile(path.join(root, name))).digest("hex");
  }
  if (args.includes("--baseline-ref")) report.baseline_commit = value("--baseline-ref");
  await fs.writeFile(output, JSON.stringify(report, null, 2) + "\n");
  process.stdout.write(JSON.stringify(report, null, 2) + "\n");
} finally {
  if (socket?.readyState === WebSocket.OPEN) {
    try { await command("Browser.close"); } catch (error) { process.stderr.write(`Browser close: ${error.message}\n`); }
    socket.close();
  }
  for (const request of pending.values()) clearTimeout(request.timeout);
  if (child.exitCode === null) child.kill();
}
