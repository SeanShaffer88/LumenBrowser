// SPDX-License-Identifier: MPL-2.0
import assert from "node:assert/strict";
import { test } from "node:test";
import { LumenSettings } from "../browser/settings-model.mjs";

function fixture() {
  const catalog = [
    { pref: "feature", type: "bool", title: "Feature" },
    { pref: "dependent", type: "bool", dependsOn: { pref: "feature", value: true } },
    { pref: "privacy", type: "bool", warning: "Reduced privacy", warnValues: [true] },
    { pref: "choice", type: "int", options: [{ value: 0 }, { value: 2 }] },
    { pref: "theme", type: "string", options: [{ value: "light" }, { value: "dark" }] },
  ];
  const defaults = new Map([["feature", false], ["dependent", false], ["privacy", false], ["choice", 0], ["theme", "light"]]);
  const values = new Map();
  const locks = new Set();
  const backend = {
    type: name => catalog.find(item => item.pref === name)?.type,
    get: name => values.has(name) ? values.get(name) : defaults.get(name),
    defaultValue: name => defaults.get(name),
    set: (name, type, value) => {
      if (locks.has(name)) {
        throw new Error("locked");
      }
      values.set(name, value);
    },
    clear: name => values.delete(name),
    locked: name => locks.has(name),
    hasUserValue: name => values.has(name),
  };
  return { model: new LumenSettings(catalog, backend), backend, values, locks };
}

const documentFor = settings => JSON.stringify({ format: "lumen-settings", version: 1, settings });

test("untrusted import validates every value before any mutation", () => {
  for (const invalid of [
    documentFor({ feature: true, choice: 3 }),
    documentFor({ feature: true, unknown: false }),
    documentFor({ choice: "2" }),
    documentFor({ theme: "<script>" }),
    documentFor({ choice: 2147483648 }),
    '{"format":"lumen-settings","version":1,"settings":{"__proto__":{}}}',
    '{"format":"lumen-settings","version":1,"settings":[]}',
    '{', "x".repeat(1024 * 1024 + 1),
  ]) {
    const { model, values } = fixture();
    assert.throws(() => model.importSettings(invalid, true));
    assert.equal(values.size, 0);
  }
});

test("privacy-reducing writes require confirmation and dependencies are enforced", () => {
  const { model, values } = fixture();
  assert.throws(() => model.set("privacy", true), error => error.code === "confirmation");
  assert.throws(() => model.set("dependent", true), error => error.code === "dependency");
  assert.equal(values.size, 0);
  model.set("feature", true);
  model.set("dependent", true);
  model.set("privacy", true, true);
  assert.equal(values.get("privacy"), true);
});

test("policy locks block direct changes and are preserved during reset and import", () => {
  const { model, locks, values } = fixture();
  values.set("feature", true);
  values.set("theme", "dark");
  locks.add("feature");
  assert.throws(() => model.set("feature", false), error => error.code === "locked");
  assert.throws(() => model.reset("feature"), error => error.code === "locked");
  assert.equal(model.restoreDefaults(), 1);
  assert.equal(values.get("feature"), true);
  const result = model.importSettings(documentFor({ feature: false, choice: 2 }), true);
  assert.deepEqual(result, { changed: 1, skipped: 1 });
  assert.equal(values.get("feature"), true);
  assert.equal(values.get("choice"), 2);
});

test("import preview reports warnings and application requires explicit confirmation", () => {
  const { model, values } = fixture();
  const text = documentFor({ privacy: true, feature: true });
  assert.equal(model.planImport(text).changes.length, 2);
  assert.deepEqual(model.planImport(text).warnings, ["Reduced privacy"]);
  assert.throws(() => model.importSettings(text), error => error.code === "confirmation");
  assert.equal(values.size, 0);
  model.importSettings(text, true);
  assert.equal(values.get("privacy"), true);
});

test("partial failed imports restore both previous values and user-branch presence", () => {
  const { model, backend, values } = fixture();
  values.set("feature", false);
  const before = new Map(values);
  const original = backend.set;
  let injected = false;
  backend.set = (name, type, value) => {
    original(name, type, value);
    if (name === "choice" && !injected) {
      injected = true;
      throw new Error("simulated partial write");
    }
  };
  assert.throws(() => model.importSettings(documentFor({ feature: true, choice: 2 }), true), /prior values restored/);
  assert.deepEqual(values, before);
});

test("failed restoration identifies the affected preference", () => {
  const { model, backend } = fixture();
  backend.set = () => { throw new Error("permission denied"); };
  backend.clear = () => { throw new Error("locked during recovery"); };
  assert.throws(() => model.importSettings(documentFor({ feature: true }), true), /restoration incomplete for: feature/);
});

test("failed reset restores already-cleared values", () => {
  const { model, backend, values } = fixture();
  values.set("feature", true);
  values.set("choice", 2);
  const before = new Map(values);
  const original = backend.clear;
  backend.clear = name => {
    if (name === "choice") {
      throw new Error("simulated failure");
    }
    original(name);
  };
  assert.throws(() => model.restoreDefaults(), /prior values restored/);
  assert.deepEqual(values, before);
});

test("export contains only allowlisted settings and reports unsupported custom values", () => {
  const { model, values } = fixture();
  values.set("choice", 999);
  values.set("profile.password", "sensitive");
  const exported = JSON.parse(model.exportSettings());
  assert.deepEqual(exported.omitted, ["choice"]);
  assert.ok(!Object.hasOwn(exported.settings, "choice"));
  assert.ok(!Object.hasOwn(exported.settings, "profile.password"));
  assert.ok(!JSON.stringify(exported).includes("sensitive"));
  const { model: recipient } = fixture();
  recipient.importSettings(JSON.stringify(exported), true);
});

test("unavailable settings are skipped rather than creating unsupported preferences", () => {
  const { model, backend, values } = fixture();
  backend.type = () => undefined;
  const result = model.importSettings(documentFor({ feature: true }), true);
  assert.deepEqual(result, { changed: 0, skipped: 1 });
  assert.equal(values.size, 0);
});
