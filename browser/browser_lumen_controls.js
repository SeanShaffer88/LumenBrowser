// SPDX-License-Identifier: MPL-2.0
"use strict";

for (const redesign of [false, true]) {
  add_task(async function lumen_controls_edit_search_reset() {
    await SpecialPowers.pushPrefEnv({
      set: [
        ["browser.settings-redesign.enabled", redesign],
        ["general.smoothScroll", true],
        ["privacy.userContext.enabled", true],
      ],
    });
    await openPreferencesViaOpenPreferencesAPI("paneLumen", {
      leaveOpen: true,
    });
    const win = gBrowser.contentWindow;
    const doc = win.document;
    try {
      const pane = win.gLumenPane;
      Assert.equal(
        doc.querySelectorAll(".lumen-row").length,
        57,
        "All catalog controls rendered"
      );
      Assert.ok(
        !doc.getElementById("lumen-controls").hidden,
        "Lumen pane is visible"
      );
      const row = pane.rows.get("general.smoothScroll");
      row.input.scrollIntoView({ block: "center" });
      await new Promise(resolve => win.requestAnimationFrame(resolve));
      EventUtils.synthesizeMouseAtCenter(row.input, {}, win);
      await TestUtils.waitForCondition(
        () => !pane.busy,
        "Preference write completed"
      );
      Assert.ok(
        !Services.prefs.getBoolPref("general.smoothScroll"),
        "User change persisted"
      );
      const search = doc.getElementById("lumen-filter");
      search.value = "smooth scrolling";
      search.dispatchEvent(new win.Event("input", { bubbles: true }));
      Assert.ok(!row.row.hidden, "Search finds the setting by its label");
      Assert.equal(
        doc.querySelectorAll(".lumen-row:not([hidden])").length,
        1,
        "Search filters other controls"
      );
      Assert.equal(pane.matchCount, 1, "Live result count matches filtering");
      search.value = "lumen-no-such-setting-xyz";
      search.dispatchEvent(new win.Event("input", { bubbles: true }));
      Assert.equal(pane.matchCount, 0, "Empty searches report zero matches");
      search.focus();
      EventUtils.synthesizeKey("KEY_Escape", {}, win);
      Assert.equal(pane.matchCount, 57, "Escape clears all filters");
      Assert.ok(
        doc.getElementById("lumen-clear-filters").disabled,
        "Clear button reflects inactive filters"
      );
      doc.getElementById("lumen-export").focus();
      EventUtils.synthesizeKey("/", {}, win);
      Assert.equal(
        doc.activeElement,
        search,
        "Slash focuses the local setting search"
      );
      search.value = "smooth scrolling";
      search.dispatchEvent(new win.Event("input", { bubbles: true }));
      row.reset.scrollIntoView({ block: "center" });
      await new Promise(resolve => win.requestAnimationFrame(resolve));
      EventUtils.synthesizeMouseAtCenter(row.reset, {}, win);
      await TestUtils.waitForCondition(() => !pane.busy, "Reset completed");
      Assert.ok(
        !Services.prefs.prefHasUserValue("general.smoothScroll"),
        "Reset restores the shipped default branch"
      );
      Services.prefs.lockPref("general.smoothScroll");
      await TestUtils.waitForCondition(
        () => row.input.disabled,
        "Policy lock notification updates the control"
      );
      Assert.ok(row.input.disabled, "Policy-managed control is disabled");
      Assert.throws(
        () => pane.model.set("general.smoothScroll", false),
        /managed by policy/,
        "Model enforces policy too"
      );
      Services.prefs.unlockPref("general.smoothScroll");
      await TestUtils.waitForCondition(
        () => !row.input.disabled,
        "Unlock restores the control"
      );
      const dependent = pane.rows.get("privacy.userContext.ui.enabled");
      Services.prefs.setBoolPref("privacy.userContext.enabled", false);
      await TestUtils.waitForCondition(
        () => dependent.input.disabled,
        "Parent notifications disable dependent controls"
      );
      await pane.action(() =>
        Services.prefs.setBoolPref("privacy.userContext.enabled", true)
      );
      Assert.ok(
        !dependent.input.disabled,
        "Busy action reconciles dependent controls"
      );
      search.value = "";
      search.dispatchEvent(new win.Event("input", { bubbles: true }));
      const modifiedOnly = doc.getElementById("lumen-modified-only");
      modifiedOnly.checked = true;
      modifiedOnly.dispatchEvent(new win.Event("change", { bubbles: true }));
      Services.prefs.setBoolPref(
        "general.smoothScroll",
        !Services.prefs.getDefaultBranch("").getBoolPref("general.smoothScroll")
      );
      Assert.ok(
        !row.row.hidden,
        "Modified-only view reacts to external changes"
      );
      row.reset.scrollIntoView({ block: "center" });
      await new Promise(resolve => win.requestAnimationFrame(resolve));
      EventUtils.synthesizeMouseAtCenter(row.reset, {}, win);
      await TestUtils.waitForCondition(
        () => !pane.busy && row.row.hidden,
        "Reset reconciles the modified-only filter"
      );
    } finally {
      Services.prefs.unlockPref("general.smoothScroll");
      BrowserTestUtils.removeTab(gBrowser.selectedTab);
      await SpecialPowers.popPrefEnv();
    }
  });
}
