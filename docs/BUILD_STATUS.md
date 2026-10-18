# Development verification status — 2026-10-18

This document records performed work and explicitly separates it from release requirements. It is not a release announcement.

| Check | Evidence / state |
|---|---|
| Project repository | SeanShaffer88/LumenBrowser; original main license preserved |
| Upstream | Full checkout of `4523d65b575546e2b588dfb8b91e3d94ebeec19a`, version `160.0a1` |
| Snapshot provenance check | Imported audit snapshots compared against bytes in the real pinned checkout |
| Real patch check | Defaults/configure/Mach telemetry patch checked and applied to the full checkout |
| Settings/Nimbus patch | Applied to the pinned full tree; frontend rebuild succeeded; full generated patch reverse-check matches the real managed files, including regional Quick Suggest defaults |
| Tooling tests | 13 Python tests passed locally |
| Settings model tests | 11 Node tests passed locally; includes explicit write/rollback postconditions and no npm dependencies |
| Settings performance | Paired isolated Edge DOM harness: preference reads 373→7 per external update, 764→26 per edit; nine correctness checks pass on both adapters. Simulated Gecko services; see PERFORMANCE.md for timings/limits |
| Development ZIP | Generated, CRC-checked, extracted and launched with a fresh profile/system-only PATH. Settings render and selected privacy defaults pass; artifact hash/limits in development-artifact-2026-10-18.json |
| Native settings performance | Final medians: external update 0.902→0.350 ms, edit 1.465→0.545 ms, filtering 0.088→0.021 ms; samples/hashes in benchmarks/results/settings-gecko-2026-10-18.json |
| Upstream lint | Zero errors, two nonblocking warnings; see PERFORMANCE.md |
| Source packaging | Deterministic archive generation, ZIP integrity and complete SHA-256 manifest tested |
| Published review | Draft PR #1 contains the foundation; Windows/Linux foundation CI passed for optimization commit `c08f954` (run `39109974632`) |
| Development host | Windows 11 Home x64, build 26300; not a Windows 10 test environment |
| MozillaBuild | 4.2.1, extracted locally from a Mozilla-signed installer; installer not executed |
| Build Python / Rust | MozillaBuild Python 3.12.10 / isolated Rust 1.99.1 |
| Toolchain bootstrap | Completed with `--no-system-changes`; compiler/SDK/state under the dedicated development directory |
| Build target | `x86_64-pc-windows-msvc`; generated `WINVER` and `_WIN32_WINNT` remain `0x0A00` |
| Native compilation | Succeeded, eight workers, 48m 54s; subsequent frontend rebuilds succeeded |
| Browser mochitests | Defaults: 33 assertions passed; controls: 22 assertions across both layouts passed; native performance: 5 assertions per adapter passed. HTTP test-profile override documented in BUILDING.md |
| UI visual/accessibility checks | Packaged pane screenshot inspected; 57 controls render and native pointer/search/reset/policy/dependency tests pass. Screen-reader/high-contrast/full visual qualification incomplete |
| Windows 10 runtime | Unverified |
| Packaged network/privacy behavior | Unverified; no zero-telemetry claim |
| Fork release identity/signing/updates | Not configured; distribution blocked |

The host uses a separate source/state directory without spaces. Build subprocesses receive an allowlisted environment; personal application credentials are not intentionally forwarded. Raw toolchain/build logs remain local and are not included in the source bundle or GitHub CI artifacts. The build candidate retains upstream security mechanisms and uses nonofficial development branding. Full release gates are in [VERIFICATION.md](VERIFICATION.md), with the work order in [DELIVERY_PLAN.md](../DELIVERY_PLAN.md).
