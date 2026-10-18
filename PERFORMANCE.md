# Performance investigation

Status: the settings-layer optimization passed a paired DOM microbenchmark and correctness checks. A native Firefox build is compiling; no browser startup, page-rendering, scrolling or memory improvement is claimed.

## Scope and baseline

The first measured path is the implemented 57-control settings pane. The baseline preference observer refreshed all controls for every preference event, while an interactive action refreshed all controls before and after the operation. Filtering rebuilt lowercased search strings from every row's DOM text on every query.

The developer harness runs the actual `browser/settings.js` and `settings-model.mjs` against real DOM elements in an isolated headless Chromium browser. Gecko preference and Fluent services are simulated; their call counts are instrumented. This can identify redundant work and compare the same JavaScript/DOM workload, but cannot establish Gecko/XPCOM costs, real Fluent latency, rendering smoothness, or whole-browser performance.

Paired comparison on Windows 11 Home x64 build 26300, Edge 155.0.4283.62, Node 24.22.0, 57 controls, 16 reported hardware threads: 20 warmup iterations, nine batches of 100 operations per scenario. Baseline UI is commit `c455485`; model/catalog are identical. Baseline runs first in the same isolated browser process, so order and JIT effects are possible. The native Firefox build concurrently used eight workers, adding CPU contention. Primary evidence is deterministic service-call counts; timings are indicative microbenchmarks. Raw samples, hashes and checks are in [the retained report](benchmarks/results/settings-ui-2026-10-18.json).

| Scenario | Baseline median ms/op (range) | Optimized median ms/op (range) | Preference reads before → after | Localization calls before → after |
|---|---:|---:|---:|---:|
| External preference update | 0.260 (0.232–0.304) | 0.002 (0.001–0.010) | 373 → 7 | 57 → 1 |
| Interactive preference change | 0.527 (0.498–0.571) | 0.121 (0.107–0.129) | 764 → 26 | 114 → 1 |
| Filtering | 0.111 (0.086–0.127) | 0.026 (0.022–0.031) | 0 → 0 | 0 → 0 |

These paths were already sub-millisecond in this synthetic environment. The optimization removes redundant work and service-boundary crossings; it demonstrates no general browsing breakthrough. Single initialization samples are retained for transparency but do not establish a startup gain. An earlier paired run also reduced reads to 7/26 and median times to 0.004/0.123/0.027 ms; only the final report matches the final source hash.

## Changes and correctness tradeoffs

Preference notifications now refresh the changed control and its transitive dependents. Actions reconcile notifications once on completion; reset/import explicitly include affected names so clearing an equal-default user value still updates the modified filter. Busy controls restore from cached state rather than rereading every preference twice. The settings model still validates policy locks, availability, dependencies and transaction postconditions on writes. The pinned upstream `Preferences::Lock` notifies preference observers when a lock changes.

Search strings and current row states are cached for this pane's lifetime. One shared MutationObserver invalidates localized label/description text; filtering reuses strings and only changes visibility when needed. This adds bounded memory for 57 cached states/strings and small dependency sets; heap cost has not been measured. No timer, worker, dependency or network service was added. The observer disconnects on cleanup. Search covers titles, descriptions and preference names, rather than transient default/status hints.

Both baseline and optimized adapters pass nine real-DOM checks: dependency disable/restore, policy lock notification, input change handler, busy disable/reconciliation, modified visibility, reset/filter reconciliation and localized search invalidation. The harness also checks control count, filtering and preference-observer cleanup. Services are simulated; actual Gecko observer/Fluent integration and native mochitests remain required. Model failure-injection tests cover write/rollback correctness independently.

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
