# Performance investigation

Status: native Windows x64 compilation, settings correctness tests and paired Gecko benchmarks passed. A development ZIP also passed extracted startup/settings checks on Windows 11. No browser startup, page-rendering, scrolling or memory improvement is claimed.

## Scope and baseline

The first measured path is the implemented 57-control settings pane. The baseline preference observer refreshed all controls for every preference event, while an interactive action refreshed all controls before and after the operation. Filtering rebuilt lowercased search strings from every row's DOM text on every query.

The developer harness runs the actual `browser/settings.js` and `settings-model.mjs` against real DOM elements in an isolated headless Chromium browser. Gecko preference and Fluent services are simulated; their call counts are instrumented. This can identify redundant work and compare the same JavaScript/DOM workload, but cannot establish Gecko/XPCOM costs, real Fluent latency, rendering smoothness, or whole-browser performance.

Paired comparison on Windows 11 Home x64 build 26300, Edge 155.0.4283.62, Node 24.22.0, 57 controls, 16 reported hardware threads: 20 warmup iterations, nine batches of 100 operations per scenario. Baseline UI is commit `c455485`; model/catalog are identical. Baseline runs first in the same isolated browser process, so order and JIT effects are possible. The native Firefox build concurrently used eight workers, adding CPU contention. Primary evidence is deterministic service-call counts; timings are indicative microbenchmarks. Raw samples, hashes and checks are in [the retained report](benchmarks/results/settings-ui-2026-10-18.json).

| Scenario | Baseline median ms/op (range) | Optimized median ms/op (range) | Preference reads before → after | Localization calls before → after |
|---|---:|---:|---:|---:|
| External preference update | 0.260 (0.232–0.304) | 0.002 (0.001–0.010) | 373 → 7 | 57 → 1 |
| Interactive preference change | 0.527 (0.498–0.571) | 0.121 (0.107–0.129) | 764 → 26 | 114 → 1 |
| Filtering | 0.111 (0.086–0.127) | 0.026 (0.022–0.031) | 0 → 0 | 0 → 0 |

These paths were already sub-millisecond in this synthetic environment. The optimization removes redundant work and service-boundary crossings; it demonstrates no general browsing breakthrough. Single initialization samples are retained for transparency but do not establish a startup gain. An earlier paired run also reduced reads to 7/26 and median times to 0.004/0.123/0.027 ms; that historical report records the source hashes at that stage. The [current DOM report](benchmarks/results/settings-ui-current-2026-10-18.json) records the formatted adapter and final catalog; do not compare its absolute timings with the earlier contended run.

## Changes and correctness tradeoffs

Preference notifications now refresh the changed control and its transitive dependents. Actions reconcile notifications once on completion; reset/import explicitly include affected names so clearing an equal-default user value still updates the modified filter. Busy controls restore from cached state rather than rereading every preference twice. The settings model still validates policy locks, availability, dependencies and transaction postconditions on writes. The pinned upstream `Preferences::Lock` notifies preference observers when a lock changes.

Search strings and current row states are cached for this pane's lifetime. One shared MutationObserver invalidates localized label/description text; filtering reuses strings and only changes visibility when needed. This adds bounded memory for 57 cached states/strings and small dependency sets; heap cost has not been measured. No timer, worker, dependency or network service was added. The observer disconnects on cleanup. Search covers titles, descriptions and preference names, rather than transient default/status hints.

Both baseline and optimized adapters pass nine real-DOM checks: dependency disable/restore, policy lock notification, input change handler, busy disable/reconciliation, modified visibility, reset/filter reconciliation and localized search invalidation. The harness also checks control count, filtering and preference-observer cleanup. Services are simulated; native default/observer/control checks now pass in Gecko too. Complete accessibility and packaged network verification remain required. Model failure-injection tests cover write/rollback correctness independently.

## Ranked opportunities

| Rank | Bottleneck | Expected impact | Risk/effort and evaluation |
|---|---|---|---|
| 1 | Whole-pane reads/writes for one changed preference | Large reduction in redundant preference/localization calls | Low-to-moderate: must update dependent controls, policy/type guards and reset/import states; benchmark plus browser tests |
| 2 | Repeated DOM text extraction/case folding during filtering | Less per-keystroke allocation/work | Low-to-moderate: localized text cache must invalidate correctly and clean up observers; benchmark plus search checks |
| 3 | Browser startup, content workloads, memory and idle activity | Potentially much larger end-user impact, currently unmeasured | Requires a completed Lumen binary and matched unmodified Firefox baseline; no speculative Gecko changes |

No experimental scheduler, allocator, SIMD/GPU rewrite, sandbox change or speculative networking change is justified by these measurements. Preserve upstream optimized components until representative profiling identifies a worthwhile path.

## Reproduce

Requires Node 22+ (tested with 24.22.0) and an installed Chromium-compatible browser for this optional developer harness. No npm packages are used. The test browser uses a new isolated profile, headless mode, extensions/sync/background networking disabled, and local-file access only for the harness. These flags do not modify Lumen's runtime settings or the user's normal browser profile.

```powershell
node benchmarks/run-settings.mjs --browser 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe' --mode both --baseline-ref c455485 --output out/performance-comparison.json
```

After an optimization, use `--mode both --baseline-ref EXACT_BASELINE_COMMIT` to compare the prior UI source with current source. The report records source hashes, scenario samples and environment. Preserve the same model/catalog and browser version for a UI-only comparison. Baseline code is read with `git show`; user source files are not reset. Outputs and isolated benchmark profiles remain under ignored `out/`.

For product-level evaluation, follow PRODUCT_GOALS.md: same hardware/OS/toolchain/build flags, fresh and representative profiles, repeated cold/warm starts, controlled pages/network/cache, memory measurements and idle/interactive traces. Use Firefox Profiler/ETW to locate actual main-thread, layout, GC, I/O or service bottlenecks before touching Gecko. Record correctness/security/compatibility results alongside gains.

## Native Gecko measurement

The generated patch registers `browser/components/preferences/tests/browser_lumen_performance.js`. After the native build and frontend integration succeed, run:

```bash
./mach mochitest --headless --setpref dom.security.https_only_mode=false browser/components/preferences/tests/browser_lumen_performance.js
```

The test uses a disposable harness profile, native preferences/Fluent and the actual pane. It emits a `LUMEN_PERFORMANCE` JSON line with all nine batch samples, build ID and test conditions for the same three scenarios. It checks completed writes and visible UI errors rather than asserting a machine-specific timing threshold. It measures synchronous adapter/DOM work and awaited action callbacks; deferred translation, layout/painting and frame latency are outside the timing boundary. The HTTP-only preference override applies to the disposable test profile because the upstream runner loads its manifest over HTTP. The shipped default remains HTTPS-only.

For a UI-only native comparison, finish the core build first. With all test browser processes closed, preserve the exact integrated adapter, substitute the baseline adapter from commit `c455485` into only `browser/components/preferences/lumen.js`, run `mach build faster`, then the benchmark. Restore the verified candidate bytes, rebuild the frontend and repeat. Check source hashes, profile conditions, logs and write assertions for both runs. Do not change the model, catalog, native binary or compiler flags between these runs. This comparison still does not establish startup or content-process gains. Never substitute files while a build or browser is using them.

## Native comparison results

Final assets on Windows 11 Home x64 build 26300, Firefox 160.0a1 build ID 20261018023517, 16 reported hardware threads. The native compiler was finished. Each adapter used a fresh disposable headless mochitest profile, the same xul.dll/firefox.exe, catalog, model, stylesheet and test; only lumen.js changed. Candidate ran first, baseline second. Each scenario used 20 warmups and nine batches of 100 operations. Other host activity was uncontrolled and fixed ordering can affect timings. This is a bounded settings microbenchmark, not a whole-browser comparison or a statistical population estimate.

| Scenario | Baseline median ms/op (range) | Optimized median ms/op (range) |
|---|---:|---:|
| External preference update | 0.902 (0.874–0.953) | 0.350 (0.324–0.446) |
| Interactive setting change | 1.465 (1.407–1.797) | 0.545 (0.522–0.595) |
| Filtering | 0.088 (0.079–0.106) | 0.021 (0.019–0.028) |

[Retained native samples, source hashes and binary hashes](benchmarks/results/settings-gecko-2026-10-18.json) identify this comparison. Both performance tests passed five assertions; the separate native defaults test passed 33 assertions and controls passed 22 assertions across both Preferences layouts. The optimized adapter was restored, hash-checked and frontend-rebuilt after baseline substitution. A prior native pair before the final stylesheet/localization polish also improved all three medians (0.818→0.435, 1.650→0.743 and 0.086→0.024 ms); its timing differences illustrate why cross-run absolute values are not interchangeable.

The native results support retaining targeted refresh, notification coalescing and search caching. Native preference writes and remaining busy-state DOM updates still account for work; their individual contributions have not been profiled. Do not weaken write/rollback checks for smaller microbenchmark numbers. Cache heap cost, frame latency, idle behavior, startup and representative content workloads still require profiling and a matched upstream browser baseline. Full changed-surface lint reports zero errors; two nonblocking warnings concern intentional forced-color CanvasText use and the pre-existing upstream Preferences import in QuickSuggest.

## QoL overlay check — 2026-10-18

The new clear-filter/search-shortcut/live-count overlay was compared with the same `c455485` baseline in Edge 155.0.4283.62, Windows 11 x64, 57 controls, 20 warmups and nine batches of 100 operations. The native eight-worker build was concurrently active, baseline ran first, and Gecko services/Fluent were simulated. [Raw samples and exact source hashes](benchmarks/results/settings-ui-qol-2026-10-18.json) retain nine correctness checks per adapter. Median ms/op: external update 0.177→0.002, interactive edit 0.371→0.083, filtering 0.071→0.018. Preference reads remain 373→7 and 764→26; filtering adds one simulated localization request when its matching count changes. Count requests are suppressed when unchanged. These timings do not establish an improvement over the prior optimized adapter or include native deferred Fluent/layout/paint cost. The refreshed native comparison below tests the formatted QoL adapter; the earlier native report remains historical evidence for its preceding build.

## Lumen Browser QoL native comparison

Windows 11 Home x64 build 26300, Lumen Browser 160.0a1 build ID `20261018054500`, 16 hardware threads; no native compilation was running during either measurement. Candidate ran first, baseline second, with fresh headless mochitest profiles, 20 warmups and nine batches of 100 operations. The binary, model, catalog, stylesheet and test were identical; only the adapter changed to/from exact baseline commit `c455485`. The candidate bytes were restored, frontend-rebuilt and the entire generated overlay reverse-checked afterward. Each performance test passed five assertions. Other host activity and fixed run order remain limitations.

| Scenario | Baseline median ms/op (range) | QoL candidate median ms/op (range) |
|---|---:|---:|
| External preference update | 1.113 (0.784–1.487) | 0.353 (0.332–0.594) |
| Interactive setting change | 1.370 (1.309–1.586) | 0.544 (0.490–0.572) |
| Filtering | 0.094 (0.086–0.131) | 0.019 (0.018–0.024) |

[Exact samples and source/binary hashes](benchmarks/results/settings-gecko-qol-2026-10-18.json) identify this pair. This supports retaining the existing targeted refresh, notification coalescing and search cache alongside the new live count and keyboard/filter controls. It does not demonstrate an additional gain over the earlier optimized adapter, nor whole-browser startup, page-load, frame latency or memory improvements. Deferred translation/layout/paint remain outside the measurement boundary. A matched unmodified Firefox binary, representative workloads and profiler/ETW traces are still needed for broader optimization decisions.

## Final public-name build verification

Repeated the adapter-only native comparison on the final public-name build `20261018070934` after native compilation completed. Conditions remain Windows 11 Home x64 build 26300, 16 hardware threads, fresh headless profiles, candidate first, baseline `c455485` second, 20 warmups and nine batches of 100 operations per scenario. The exact same native binaries, model, catalog, stylesheet and test served both runs. Other host activity was uncontrolled. Both tests passed five assertions; candidate source was restored, frontend-rebuilt and the full overlay reverse-checked.

| Scenario | Baseline median ms/op (range) | Final candidate median ms/op (range) |
|---|---:|---:|
| External preference update | 0.844 (0.817–0.922) | 0.410 (0.396–0.470) |
| Interactive setting change | 1.551 (1.414–1.718) | 0.611 (0.578–0.674) |
| Filtering | 0.090 (0.079–0.106) | 0.023 (0.019–0.031) |

[Final samples and source/binary hashes](benchmarks/results/settings-gecko-final-2026-10-18.json) identify this comparison. Earlier reports above are historical measurements, not measurements of this final binary. The tested improvement retains targeted preference refresh, coalesced notifications and cached localized search text with the QoL controls. No additional improvement over earlier optimized adapters is claimed. Deferred Fluent work, layout, paint, startup, content loading, memory and idle CPU are outside this benchmark.
