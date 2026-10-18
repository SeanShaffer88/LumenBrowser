/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */
export class SettingsError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}

export class LumenSettings {
  constructor(catalog, backend) {
    this.catalog = new Map(catalog.map(item => [item.pref, item]));
    if (this.catalog.size !== catalog.length) {
      throw new SettingsError("schema", "Duplicate setting names");
    }
    this.backend = backend;
  }

  definition(pref) {
    const item = this.catalog.get(pref);
    if (!item) {
      throw new SettingsError("unknown", `Unsupported setting: ${pref}`);
    }
    return item;
  }

  validate(pref, value) {
    const item = this.definition(pref);
    const expected = { bool: "boolean", int: "number", string: "string" }[
      item.type
    ];
    if (
      typeof value !== expected ||
      (item.type === "int" &&
        (!Number.isInteger(value) || value < -2147483648 || value > 2147483647))
    ) {
      throw new SettingsError("type", `Invalid value type: ${pref}`);
    }
    if (
      item.options &&
      !item.options.some(option => Object.is(option.value, value))
    ) {
      throw new SettingsError(
        "range",
        `Value is outside supported choices: ${pref}`
      );
    }
    return value;
  }

  state(pref) {
    const item = this.definition(pref);
    const available = this.backend.type(pref) === item.type;
    return {
      available,
      value: available ? this.backend.get(pref, item.type) : undefined,
      defaultValue: available
        ? this.backend.defaultValue(pref, item.type)
        : undefined,
      locked: this.backend.locked(pref),
      modified: this.backend.hasUserValue(pref),
      dependencyMet:
        !item.dependsOn ||
        Object.is(this.state(item.dependsOn.pref).value, item.dependsOn.value),
    };
  }

  needsConfirmation(pref, value) {
    const item = this.definition(pref);
    return Boolean(
      item.warning &&
      item.warnValues.includes(value) &&
      !Object.is(this.state(pref).value, value)
    );
  }

  assertWritable(pref) {
    const state = this.state(pref);
    if (!state.available) {
      throw new SettingsError(
        "unavailable",
        `Setting is unavailable in this build: ${pref}`
      );
    }
    if (state.locked) {
      throw new SettingsError(
        "locked",
        `Setting is managed by policy: ${pref}`
      );
    }
    return state;
  }

  set(pref, value, confirmed = false) {
    this.validate(pref, value);
    const state = this.assertWritable(pref);
    if (!state.dependencyMet) {
      throw new SettingsError(
        "dependency",
        `Enable the parent feature first: ${pref}`
      );
    }
    if (this.needsConfirmation(pref, value) && !confirmed) {
      throw new SettingsError("confirmation", this.definition(pref).warning);
    }
    this.transaction([{ pref, value }]);
  }

  reset(pref) {
    this.assertWritable(pref);
    this.transaction([{ pref }], true);
  }

  transaction(changes, clear = false) {
    const previous = changes.map(({ pref }) => {
      const state = this.assertWritable(pref);
      return { pref, value: state.value, modified: state.modified };
    });
    let completed = 0;
    try {
      for (const change of changes) {
        this.assertWritable(change.pref);
        // Include a possibly partially completed backend write in recovery.
        completed++;
        if (clear) {
          this.backend.clear(change.pref);
        } else {
          this.backend.set(
            change.pref,
            this.definition(change.pref).type,
            change.value
          );
        }
        if (
          clear
            ? this.backend.hasUserValue(change.pref)
            : !Object.is(
                this.backend.get(
                  change.pref,
                  this.definition(change.pref).type
                ),
                change.value
              )
        ) {
          throw new SettingsError(
            "postcondition",
            `Preference write was not applied: ${change.pref}`
          );
        }
      }
    } catch (error) {
      const failed = [];
      for (const old of previous.slice(0, completed).reverse()) {
        try {
          if (old.modified) {
            this.backend.set(
              old.pref,
              this.definition(old.pref).type,
              old.value
            );
          } else {
            this.backend.clear(old.pref);
          }
          if (
            !Object.is(
              this.backend.get(old.pref, this.definition(old.pref).type),
              old.value
            ) ||
            this.backend.hasUserValue(old.pref) !== old.modified
          ) {
            throw new SettingsError(
              "recovery",
              "Previous preference state was not restored"
            );
          }
        } catch (restoreError) {
          failed.push(`${old.pref} (${restoreError.message})`);
        }
      }
      throw new SettingsError(
        "transaction",
        failed.length
          ? `Change failed; restoration incomplete for: ${failed.join(", ")}`
          : `Change failed; prior values restored. ${error.message}`
      );
    }
    return changes.length;
  }

  restoreDefaults() {
    const changes = [];
    for (const pref of this.catalog.keys()) {
      const state = this.state(pref);
      if (state.available && state.modified && !state.locked) {
        changes.push({ pref });
      }
    }
    return this.transaction(changes, true);
  }

  exportSettings() {
    const settings = {};
    const omitted = [];
    for (const pref of this.catalog.keys()) {
      const state = this.state(pref);
      try {
        if (!state.available) {
          throw new SettingsError("unavailable", pref);
        }
        settings[pref] = this.validate(pref, state.value);
      } catch (error) {
        if (!(error instanceof SettingsError)) {
          throw error;
        }
        omitted.push(pref);
      }
    }
    return JSON.stringify(
      { format: "lumen-settings", version: 1, settings, omitted },
      null,
      2
    );
  }

  planImport(text) {
    if (typeof text !== "string" || text.length > 1024 * 1024) {
      throw new SettingsError(
        "format",
        "Settings file exceeds the 1 MiB limit"
      );
    }
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      throw new SettingsError("format", "Settings file is not valid JSON");
    }
    if (
      !data ||
      data.format !== "lumen-settings" ||
      data.version !== 1 ||
      !data.settings ||
      Array.isArray(data.settings) ||
      typeof data.settings !== "object" ||
      Object.keys(data).some(
        key => !["format", "version", "settings", "omitted"].includes(key)
      )
    ) {
      throw new SettingsError(
        "format",
        "Unsupported Lumen settings file format"
      );
    }
    const changes = [];
    const warnings = [];
    let skipped = 0;
    for (const [pref, value] of Object.entries(data.settings)) {
      this.validate(pref, value);
      const state = this.state(pref);
      if (!state.available || state.locked) {
        skipped++;
      } else if (!Object.is(state.value, value)) {
        changes.push({ pref, value });
        if (this.needsConfirmation(pref, value)) {
          warnings.push(this.definition(pref).warning);
        }
      }
    }
    return { changes, warnings: [...new Set(warnings)], skipped };
  }

  importSettings(text, confirmed = false) {
    const plan = this.planImport(text);
    if (!confirmed) {
      throw new SettingsError(
        "confirmation",
        "Review and confirm imported changes first"
      );
    }
    return { changed: this.transaction(plan.changes), skipped: plan.skipped };
  }
}
