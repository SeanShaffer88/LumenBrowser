// SPDX-License-Identifier: MPL-2.0
"use strict";

for (const redesign of [false, true]) {
  add_task(async function lumen_controls_edit_search_reset() {
    await SpecialPowers.pushPrefEnv({ set: [
      ["browser.settings-redesign.enabled", redesign],
      ["general.smoothScroll", true],
    ] });
    await openPreferencesViaOpenPreferencesAPI("paneLumen", { leaveOpen: true });
    const win = gBrowser.contentWindow;
    const doc = win.document;
    try {
      const pane = win.gLumenPane;
      Assert.equal(doc.querySelectorAll(".lumen-row").length, 57, "All catalog controls rendered");
      Assert.ok(!doc.getElementById("lumen-controls").hidden, "Lumen pane is visible");
      const row = pane.rows.get("general.smoothScroll");
      EventUtils.synthesizeMouseAtCenter(row.input, {}, win);
      await TestUtils.waitForCondition(() => !pane.busy, "Preference write completed");
      Assert.ok(!Services.prefs.getBoolPref("general.smoothScroll"), "User change persisted");
      const search = doc.getElementById("lumen-filter");
      search.value = "smooth scrolling";
      search.dispatchEvent(new win.Event("input", { bubbles: true }));
      Assert.ok(!row.row.hidden, "Search finds the setting by its label");
      Assert.equal(doc.querySelectorAll(".lumen-row:not([hidden])").length, 1, "Search filters other controls");
      EventUtils.synthesizeMouseAtCenter(row.reset, {}, win);
      await TestUtils.waitForCondition(() => !pane.busy, "Reset completed");
      Assert.ok(!Services.prefs.prefHasUserValue("general.smoothScroll"), "Reset restores the shipped default branch");
      Services.prefs.lockPref("general.smoothScroll");
      pane.refresh();
      Assert.ok(row.input.disabled, "Policy-managed control is disabled");
      Assert.throws(() => pane.model.set("general.smoothScroll", false), /managed by policy/, "Model enforces policy too");
    } finally {
      Services.prefs.unlockPref("general.smoothScroll");
      BrowserTestUtils.removeTab(gBrowser.selectedTab);
      await SpecialPowers.popPrefEnv();
    }
  });
}
