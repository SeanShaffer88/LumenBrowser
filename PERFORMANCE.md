# Performance investigation

Status: measurement and optimization of the Lumen settings layer are in progress. A native Firefox build is compiling; no browser startup, page-rendering, scrolling or memory improvement is claimed.

## Scope and baseline

The first measured path is the implemented 57-control settings pane. Its current preference observer refreshes all controls for every preference event, while an interactive action refreshes all controls before and after the operation. Filtering rebuilds lowercased search strings from every row's DOM text on every query.

The developer harness runs the actual `browser/settings.js` and `settings-model.mjs` against real DOM elements in an isolated headless Chromium browser. Gecko preference and Fluent services are simulated; their call counts are instrumented. This can identify redundant work and compare the same JavaScript/DOM workload, but cannot establish Gecko/XPCOM costs, real Fluent latency, rendering smoothness, or whole-browser performance.

Initial baseline on Windows 11 x64, Edge 155.0.4283.62, Node 24.22.0, 57 controls, 16 reported hardware threads: 20 warmup iterations, nine batches of 100 operations per scenario. The native Firefox build was concurrently using eight workers, so absolute timing is subject to CPU contention. Primary evidence is deterministic service-call counts; timings are indicative microbenchmarks.

| Scenario | Median ms/operation | Preference reads/operation | Localization calls/operation |
|---|---:|---:|---:|
| External preference update | 0.262 | 373 | 57 |
| Interactive preference change | 0.549 | 764 | 114 |
| Filtering | 0.109 | 0 | 0 |

These paths were already sub-millisecond in this synthetic environment. The opportunity is to remove redundant work and native-boundary crossings, not claim a general browsing breakthrough. Candidate changes will be retained only after correctness checks and a paired before/after run.

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
node benchmarks/run-settings.mjs --browser 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe' --mode baseline --output out/performance-baseline.json
```

After an optimization, use `--mode both --baseline-ref EXACT_BASELINE_COMMIT` to compare the prior UI source with current source. The report records source hashes, scenario samples and environment. Preserve the same model/catalog and browser version for a UI-only comparison. Baseline code is read with `git show`; user source files are not reset. Outputs and isolated benchmark profiles remain under ignored `out/`.

For product-level evaluation, follow PRODUCT_GOALS.md: same hardware/OS/toolchain/build flags, fresh and representative profiles, repeated cold/warm starts, controlled pages/network/cache, memory measurements and idle/interactive traces. Use Firefox Profiler/ETW to locate actual main-thread, layout, GC, I/O or service bottlenecks before touching Gecko. Record correctness/security/compatibility results alongside gains.
