// SPDX-License-Identifier: MPL-2.0
"use strict";

add_task(async function lumen_settings_performance_samples() {
  await SpecialPowers.pushPrefEnv({ set: [["general.smoothScroll", true]] });
  await openPreferencesViaOpenPreferencesAPI("paneLumen", { leaveOpen: true });
  const win = gBrowser.contentWindow;
  const pane = win.gLumenPane;
  const doc = win.document;
  async function measure(callback) {
    for (let i = 0; i < 20; i++) {
      await callback(i);
    }
    const samples = [];
    for (let batch = 0; batch < 9; batch++) {
      const start = win.performance.now();
      for (let i = 0; i < 100; i++) {
        await callback(i);
      }
      samples.push((win.performance.now() - start) / 100);
    }
    const sorted = [...samples].sort((a, b) => a - b);
    return {
      median_ms: sorted[4],
      min_ms: sorted[0],
      max_ms: sorted[8],
      samples_ms: samples,
    };
  }
  try {
    Assert.equal(pane.rows.size, 57, "Measure the complete settings pane");
    const report = {
      runtime: Services.appinfo.version,
      build_id: Services.appinfo.appBuildID,
      services:
        "Native Gecko preferences and Fluent; headless browser-chrome test",
      batches: 9,
      iterations_per_batch: 100,
      warmup_iterations: 20,
      external_preference_update: await measure(i =>
        Services.prefs.setBoolPref("general.smoothScroll", !!(i % 2))
      ),
      interactive_change: await measure(i =>
        pane.action(
          () => pane.model.set("general.smoothScroll", !!(i % 2)),
          ["general.smoothScroll"]
        )
      ),
      filtering: await measure(i => {
        doc.getElementById("lumen-filter").value =
          i % 2 ? "smooth scrolling" : "privacy";
        pane.filter();
      }),
    };
    Assert.ok(!pane.busy, "Measured actions completed");
    Assert.ok(
      doc.getElementById("lumen-error").hidden,
      "Measured writes had no UI error"
    );
    Assert.ok(
      Services.prefs.getBoolPref("general.smoothScroll"),
      "Last measured write applied"
    );
    info("LUMEN_PERFORMANCE " + JSON.stringify(report));
  } finally {
    BrowserTestUtils.removeTab(gBrowser.selectedTab);
    await SpecialPowers.popPrefEnv();
  }
});
