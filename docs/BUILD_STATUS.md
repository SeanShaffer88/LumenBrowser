# Development verification status — 2026-10-18

This document records performed work and explicitly separates it from release requirements. It is not a release announcement.

| Check | Evidence / state |
|---|---|
| Project repository | SeanShaffer88/LumenBrowser; original main license preserved |
| Upstream | Full checkout of `4523d65b575546e2b588dfb8b91e3d94ebeec19a`, version `160.0a1` |
| Snapshot provenance check | Imported audit snapshots compared against bytes in the real pinned checkout |
| Real patch check | Defaults/configure/Mach telemetry patch checked and applied to the full checkout |
| Settings/Nimbus patch | Applied to the pinned full tree; frontend rebuild succeeded; full generated patch reverse-check matches the real managed files, including regional Quick Suggest defaults |
| Tooling tests | 16 Python tests passed locally, including version-resource preservation and binary/text patch round trips |
| Settings model tests | 11 Node tests passed locally; includes explicit write/rollback postconditions and no npm dependencies |
| Settings performance | Paired isolated Edge DOM harness: preference reads 373→7 per external update, 764→26 per edit; nine correctness checks pass on both adapters. Simulated Gecko services; see PERFORMANCE.md for timings/limits |
| Development ZIP | Generated, CRC-checked, extracted and launched with a fresh profile/system-only PATH. Settings render and selected privacy defaults pass; current artifact hashes/limits in lumen-artifacts-2026-10-18.json; development-artifact-2026-10-18.json is historical |
| Native settings performance | Final public-name medians: external update 0.844→0.410 ms, edit 1.551→0.611 ms, filtering 0.090→0.023 ms; samples/hashes in benchmarks/results/settings-gecko-final-2026-10-18.json |
| Upstream lint | Zero errors, two nonblocking warnings; see PERFORMANCE.md |
| Source packaging | Deterministic archive generation, ZIP integrity and complete SHA-256 manifest tested |
| Published review | Draft PR #1 contains the foundation; Windows/Linux foundation CI passed for optimization commit `c08f954` (run `39109974632`) |
| Development host | Windows 11 Home x64, build 26300; not a Windows 10 test environment |
| MozillaBuild | 4.2.1, extracted locally from a Mozilla-signed installer; installer not executed |
| Build Python / Rust | MozillaBuild Python 3.12.10 / isolated Rust 1.99.1 |
| Toolchain bootstrap | Completed with `--no-system-changes`; compiler/SDK/state under the dedicated development directory |
| Build target | `x86_64-pc-windows-msvc`; generated `WINVER` and `_WIN32_WINNT` remain `0x0A00` |
| Native compilation | Succeeded, eight workers, 48m 54s; subsequent frontend rebuilds succeeded |
| Browser mochitests | Defaults: 35 assertions passed; controls: 32 assertions across both layouts passed; native performance: 5 assertions per adapter passed. HTTP test-profile override documented in BUILDING.md |
| UI visual/accessibility checks | Packaged pane screenshot inspected; 57 controls render and native pointer/search/reset/policy/dependency tests pass. Screen-reader/high-contrast/full visual qualification incomplete |
| Windows 10 runtime | Unverified |
| Packaged network/privacy behavior | Unverified; no zero-telemetry claim |
| Fork release identity/signing/updates | Lumen Browser branding/identity and per-user installer verified on this Windows 11 host. Signing/update service remain unconfigured; distribution blocked |

The host uses a separate source/state directory without spaces. Build subprocesses receive an allowlisted environment; personal application credentials are not intentionally forwarded. Raw toolchain/build logs remain local and are not included in the source bundle or GitHub CI artifacts. The build candidate retains upstream security mechanisms and uses nonofficial development branding. Full release gates are in [VERIFICATION.md](VERIFICATION.md), with the work order in [DELIVERY_PLAN.md](../DELIVERY_PLAN.md).

## Current branding/QoL batch

The public name is Lumen Browser; original black/red mechanical-bezel assets, distinct private-window icons, banner and native wizard artwork are implemented. All 19 raster assets regenerate byte-for-byte. Settings add clear/Escape, scoped `/` focus and a polite matching count without timers or new dependencies. The complete generated overlay passes fixture application/reversal, 16 Python tests and 11 model tests; the real tree passes the full patch reverse-check.

The final native build `20261018070934` passes 35 defaults/identity assertions, 32 controls assertions across both layouts, and five performance assertions per adapter. Main/private executable ProductName and CompanyName now match the public identity. A discovered upstream resource dependency omission was corrected; native resource/shell lint reports zero errors and warnings. Earlier changed-surface lint's two nonblocking warnings remain documented in PERFORMANCE.md.

The final ZIP passes CRC and fresh-profile/system-only-PATH startup. The full unsigned self-extracting installer passes `/Help` without installation, foreign-browser guard exit 2 with sentinel preservation, a path containing spaces, `/NoShortcuts` precedence, all 62 payload hashes, repeat install, the desktop shortcut and `Lumen Browser\Lumen Browser.lnk` Start Menu placement. Native icon discovery sees Desktop and Programs; applying/reverting the optional retro icon leaves the links in place. Installation telemetry output is absent. Default-browser choices remain unchanged. Uninstall removes core files and owned links while preserving the owned profile sentinel and default choices. These are scoped postconditions, not a complete recovery or network guarantee.

[Exact artifact hashes and sanitized verification evidence](lumen-artifacts-2026-10-18.json) identify the tested development build. The earlier NSIS component probe in installer-probe-2026-10-18.json is historical and separate. Signing, supported baseline selection, Windows 10 execution, full privacy/accessibility qualification and authenticated updates/recovery remain release blockers.

Repository change whitespace checks pass excluding byte-preserved audit inputs. A full staged check reports the upstream SFX source’s existing CRLF lines as trailing whitespace (596 lines); those reference bytes remain unchanged and hash-verified. NSIS packaging also retains upstream warning 9000 for the internal setup.exe compatibility-shim filename. Neither is reported as a clean full-tree lint result.
