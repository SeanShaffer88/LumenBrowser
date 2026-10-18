// SPDX-License-Identifier: MPL-2.0
/* import-globals-from preferences.js */
"use strict";

var gLumenPane = {
  init() {
    const { LumenSettings } = ChromeUtils.importESModule(
      "chrome://browser/content/preferences/lumen/settings-model.mjs"
    );
    const { LUMEN_CATALOG } = ChromeUtils.importESModule(
      "chrome://browser/content/preferences/lumen/catalog.mjs"
    );
    this.catalog = LUMEN_CATALOG;
    this.rows = new Map();
    this.groups = [];
    this.observed = [];
    this.states = new Map();
    this.dirty = new Set();
    this.dependents = new Map();
    this.allNames = new Set(this.catalog.map(item => item.pref));
    for (const item of this.catalog) {
      if (item.dependsOn) {
        const parent = item.dependsOn.pref;
        if (!this.dependents.has(parent)) {
          this.dependents.set(parent, new Set());
        }
        this.dependents.get(parent).add(item.pref);
      }
    }
    this.busy = false;
    const defaults = Services.prefs.getDefaultBranch("");
    const methods = { bool: "Bool", int: "Int", string: "String" };
    const types = { 128: "bool", 64: "int", 32: "string" };
    this.model = new LumenSettings(this.catalog, {
      type: name => {
        const type = defaults.getPrefType(name);
        return type === Services.prefs.getPrefType(name) ? types[type] : undefined;
      },
      get: (name, type) => Services.prefs[`get${methods[type]}Pref`](name),
      defaultValue: (name, type) => defaults[`get${methods[type]}Pref`](name),
      set: (name, type, value) => Services.prefs[`set${methods[type]}Pref`](name, value),
      clear: name => Services.prefs.clearUserPref(name),
      locked: name => Services.prefs.prefIsLocked(name),
      hasUserValue: name => Services.prefs.prefHasUserValue(name),
    });
    const categories = [...new Set(this.catalog.map(item => item.category))];
    for (const category of categories) {
      const option = this.element("option", `lumen-category-${category}`);
      option.value = category;
      this.node("lumen-category").append(option);
      for (const advanced of [false, true]) {
        const items = this.catalog.filter(item => item.category === category && !!item.advanced === advanced);
        if (!items.length) {
          continue;
        }
        const group = this.element("section");
        group.className = "lumen-group";
        const heading = this.element("h2", `lumen-category-${category}`);
        heading.id = `lumen-group-${advanced ? "advanced" : "standard"}-${category}`;
        group.setAttribute("aria-labelledby", heading.id);
        group.append(heading);
        this.node(advanced ? "lumen-advanced-rows" : "lumen-standard").append(group);
        const rowElements = items.map(item => this.buildRow(item, group));
        this.groups.push({ group, rows: rowElements });
      }
    }
    window.addEventListener("unload", () => this.cleanup(), { once: true });
    this.searchObserver = new MutationObserver(records => {
      const names = new Set();
      for (const record of records) {
        const element = record.target.nodeType === Node.ELEMENT_NODE ? record.target : record.target.parentElement;
        const pref = element?.closest(".lumen-row")?.dataset.pref;
        if (pref) {
          names.add(pref);
        }
      }
      for (const pref of names) {
        this.cacheSearchText(pref);
      }
      if (this.node("lumen-filter").value) {
        this.filter();
      }
    });
    for (const { label, description } of this.rows.values()) {
      for (const element of [label, description]) {
        this.searchObserver.observe(element, { childList: true, characterData: true, subtree: true });
      }
    }
    for (const item of this.catalog) {
      Services.prefs.addObserver(item.pref, this);
      this.observed.push(item.pref);
    }
    this.node("lumen-filter").addEventListener("input", () => this.filter());
    this.node("lumen-category").addEventListener("change", () => this.filter());
    this.node("lumen-modified-only").addEventListener("change", () => this.filter());
    this.node("lumen-reset-all").addEventListener("click", () => this.action(async () => {
      const title = await document.l10n.formatValue("lumen-title");
      const message = await document.l10n.formatValue("lumen-reset-confirm");
      if (Services.prompt.confirm(window, title, message)) {
        this.status("lumen-reset-complete", { count: this.model.restoreDefaults() });
      }
    }, this.allNames));
    this.node("lumen-export").addEventListener("click", () => this.action(() => this.exportSettings()));
    this.node("lumen-import").addEventListener("click", () => this.node("lumen-import-file").click());
    this.node("lumen-import-file").addEventListener("change", () => this.action(() => this.importSettings(), this.allNames));
    this.refresh();
  },

  node(id) {
    return document.getElementById(id);
  },

  element(tag, l10nId) {
    const element = document.createElementNS("http://www.w3.org/1999/xhtml", tag);
    if (l10nId) {
      document.l10n.setAttributes(element, l10nId);
    }
    return element;
  },

  buildRow(item, group) {
    const index = this.catalog.indexOf(item);
    const prefix = `lumen-setting-${index}`;
    const row = this.element("article");
    row.className = "lumen-row";
    row.dataset.pref = item.pref;
    const line = this.element("div");
    line.className = "lumen-control-line";
    const label = this.element("label", `${prefix}-title`);
    label.className = "lumen-label";
    label.htmlFor = `${prefix}-control`;
    const input = this.element(item.type === "bool" ? "input" : "select");
    input.id = label.htmlFor;
    if (item.type === "bool") {
      input.type = "checkbox";
    } else {
      item.options.forEach((option, i) => {
        const element = this.element("option", `${prefix}-option-${i}`);
        element.value = JSON.stringify(option.value);
        input.append(element);
      });
    }
    const description = this.element("p", `${prefix}-description`);
    description.id = `${prefix}-description`;
    description.className = "lumen-description";
    const hint = this.element("p");
    hint.id = `${prefix}-hint`;
    hint.className = "lumen-default";
    input.setAttribute("aria-describedby", `${description.id} ${hint.id}`);
    const reset = this.element("button", "lumen-reset");
    reset.className = "lumen-reset";
    document.l10n.setAttributes(reset, "lumen-reset-setting", { name: item.title });
    reset.addEventListener("click", () => this.action(() => {
      this.model.reset(item.pref);
      this.status("lumen-reset-one");
    }, [item.pref]));
    input.addEventListener("change", () => {
      const value = item.type === "bool" ? input.checked : JSON.parse(input.value);
      this.action(async () => {
        let confirmed = false;
        if (this.model.needsConfirmation(item.pref, value)) {
          const title = await document.l10n.formatValue("lumen-change-confirm");
          const warning = await document.l10n.formatValue(`${prefix}-warning`);
          confirmed = Services.prompt.confirm(window, title, warning);
          if (!confirmed) {
            return;
          }
        }
        this.model.set(item.pref, value, confirmed);
        this.status("lumen-saved");
      }, [item.pref]);
    });
    line.append(label, input, reset);
    row.append(line, description, hint);
    if (item.restart) {
      row.append(this.element("p", "lumen-restart"));
    }
    group.append(row);
    this.rows.set(item.pref, { row, input, hint, reset, label, description });
    this.cacheSearchText(item.pref);
    return row;
  },

  cacheSearchText(pref) {
    const entry = this.rows.get(pref);
    const item = this.model.definition(pref);
    entry.searchText = `${item.title} ${item.description} ${pref} ${entry.label.textContent} ${entry.description.textContent}`.toLocaleLowerCase();
  },

  relatedNames(names) {
    const related = new Set([...names].filter(name => this.allNames.has(name)));
    const queue = [...related];
    while (queue.length) {
      for (const dependent of this.dependents.get(queue.pop()) ?? []) {
        if (!related.has(dependent)) {
          related.add(dependent);
          queue.push(dependent);
        }
      }
    }
    return related;
  },

  refresh(names = null) {
    const items = names ? [...names].map(name => this.model.definition(name)) : this.catalog;
    for (const item of items) {
      const state = this.model.state(item.pref);
      this.states.set(item.pref, state);
      const { row, input, hint, reset } = this.rows.get(item.pref);
      input.disabled = this.busy || !state.available || state.locked || !state.dependencyMet;
      reset.disabled = this.busy || !state.available || state.locked || !state.modified;
      row.dataset.modified = String(state.modified);
      if (item.type === "bool") {
        input.checked = !!state.value;
      } else {
        input.querySelector("[data-custom]")?.remove();
        const value = JSON.stringify(state.value);
        if (state.available && !item.options.some(option => Object.is(option.value, state.value))) {
          const custom = this.element("option", "lumen-custom-value");
          custom.value = value;
          custom.disabled = true;
          custom.dataset.custom = "true";
          input.append(custom);
        }
        input.value = value ?? "";
      }
      if (!state.available) {
        document.l10n.setAttributes(hint, "lumen-unavailable");
      } else if (state.locked) {
        document.l10n.setAttributes(hint, "lumen-managed");
      } else if (!state.dependencyMet) {
        const parent = this.model.definition(item.dependsOn.pref);
        document.l10n.setAttributes(hint, "lumen-dependency", { parent: parent.title });
      } else if (item.type === "bool") {
        document.l10n.setAttributes(hint, "lumen-default-boolean", { value: String(state.defaultValue) });
      } else {
        const option = item.options.find(entry => Object.is(entry.value, state.defaultValue));
        document.l10n.setAttributes(hint, "lumen-default-choice", { value: option?.label ?? String(state.defaultValue) });
      }
    }
    if (!names || this.node("lumen-modified-only").checked) {
      this.filter();
    }
  },

  filter() {
    const query = this.node("lumen-filter").value.trim().toLocaleLowerCase();
    const category = this.node("lumen-category").value;
    const modifiedOnly = this.node("lumen-modified-only").checked;
    let count = 0;
    let advancedMatch = false;
    for (const item of this.catalog) {
      const { row, searchText } = this.rows.get(item.pref);
      const hidden = !((!query || searchText.includes(query)) &&
        (category === "all" || item.category === category) &&
        (!modifiedOnly || this.states.get(item.pref)?.modified));
      if (row.hidden !== hidden) {
        row.hidden = hidden;
      }
      if (!row.hidden) {
        count++;
        advancedMatch ||= !!item.advanced;
      }
    }
    for (const { group, rows } of this.groups) {
      group.hidden = rows.every(row => row.hidden);
    }
    this.node("lumen-advanced").hidden = !advancedMatch;
    if ((query || modifiedOnly || category !== "all") && advancedMatch) {
      this.node("lumen-advanced").open = true;
    }
    this.node("lumen-no-results").hidden = count !== 0;
  },

  observe(subject, topic, pref) {
    if (!this.allNames.has(pref)) {
      return;
    }
    if (this.busy) {
      this.dirty.add(pref);
    } else {
      this.refresh(this.relatedNames([pref]));
    }
  },

  status(id, args) {
    document.l10n.setAttributes(this.node("lumen-status"), id, args);
  },

  setBusy(busy) {
    this.busy = busy;
    this.node("lumen-controls").toggleAttribute("aria-busy", busy);
    if (busy) {
      this.node("lumen-controls").setAttribute("aria-busy", "true");
    }
    for (const [pref, { input, reset }] of this.rows) {
      const state = this.states.get(pref);
      input.disabled = busy || !state?.available || state.locked || !state.dependencyMet;
      reset.disabled = busy || !state?.available || state.locked || !state.modified;
    }
    for (const id of ["lumen-import", "lumen-export", "lumen-reset-all"]) {
      this.node(id).disabled = busy;
    }
  },

  async action(callback, names = []) {
    if (this.busy) {
      return;
    }
    this.dirty.clear();
    this.setBusy(true);
    this.node("lumen-error").hidden = true;
    this.node("lumen-status").removeAttribute("data-l10n-id");
    this.node("lumen-status").textContent = "";
    try {
      await callback();
    } catch (error) {
      this.node("lumen-error").textContent = error.message;
      this.node("lumen-error").hidden = false;
    } finally {
      this.busy = false;
      try {
        this.refresh(this.relatedNames([...names, ...this.dirty]));
      } catch (error) {
        this.node("lumen-error").textContent = error.message;
        this.node("lumen-error").hidden = false;
      } finally {
        this.dirty.clear();
        this.setBusy(false);
      }
    }
  },

  exportSettings() {
    const text = this.model.exportSettings();
    if (this.exportUrl) {
      URL.revokeObjectURL(this.exportUrl);
    }
    this.exportUrl = URL.createObjectURL(new Blob([text], { type: "application/json" }));
    const anchor = this.element("a");
    anchor.href = this.exportUrl;
    anchor.download = "lumen-settings.json";
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    this.status("lumen-export-complete", { count: JSON.parse(text).omitted.length });
  },

  async importSettings() {
    const input = this.node("lumen-import-file");
    const file = input.files[0];
    input.value = "";
    if (!file) {
      return;
    }
    if (file.size > 1024 * 1024) {
      throw new Error(await document.l10n.formatValue("lumen-file-too-large"));
    }
    const text = await file.text();
    const plan = this.model.planImport(text);
    const message = await document.l10n.formatValue("lumen-import-confirm", {
      count: plan.changes.length, skipped: plan.skipped,
    });
    const title = await document.l10n.formatValue("lumen-change-confirm");
    if (Services.prompt.confirm(window, title, [message, ...plan.warnings].join("\n\n"))) {
      const result = this.model.importSettings(text, true);
      this.status("lumen-import-complete", { count: result.changed, skipped: result.skipped });
    }
  },

  cleanup() {
    this.searchObserver?.disconnect();
    for (const pref of this.observed) {
      try {
        Services.prefs.removeObserver(pref, this);
      } catch (error) {
        console.error(`Lumen observer cleanup failed for ${pref}`, error);
      }
    }
    this.observed.length = 0;
    if (this.exportUrl) {
      URL.revokeObjectURL(this.exportUrl);
    }
  },
};
