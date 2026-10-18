# Changelog

Entries record each development stage; current implementation and verification are in docs/BUILD_STATUS.md.

## Unreleased — development foundation, 2026-10-18

- Integrate into SeanShaffer88/LumenBrowser while preserving the existing MPL-2.0 license.
- Establish Windows 10 and newer as the compatibility target, with a dedicated release matrix.
- Add Windows/Linux foundation CI and deterministic source bundles with SHA-256 inventories; CI does not build a browser.
- Add an integrated 57-control settings pane with search, categories, advanced disclosure, reset, policy/dependency guards, and validated settings import/export with rollback handling.
- Disable Mach telemetry initialization and setup through the upstream no-op implementation; browser telemetry remains separately unverified.
- Disable the optional Nimbus Labs/rollout/study gates after tracing an experiment-loader path that remained enabled independently of telemetry preferences.
- Verify preference write and rollback postconditions so silent failures cannot be reported as successful changes or recovery.
- Prepare a full pinned source checkout and isolated MozillaBuild/Rust/compiler environment; native build is in progress.
- Adopt product quality gates and a documented critical path that prioritizes build verification over further discretionary features.

- Pin Firefox main revision `4523d65b575546e2b588dfb8b91e3d94ebeec19a` (`160.0a1`) with selected hash-verified source snapshots.
- Add 31 explained privacy/security default preferences and a deterministic source patch generator.
- Generate Health Reporter/Normandy configure changes and a registered browser default-preference test.
- Add candidate Windows x64 full-build configuration, privacy inventory, failure-injection tooling tests, and release procedures.
- No binary, installer, browser test result, complete telemetry-removal guarantee, finished branding, update service, migration implementation, or supported platform release.

## Settings responsiveness investigation — 2026-10-18

- Refresh changed preferences and their dependent controls, reconcile busy notifications once, and cache search text with localization invalidation. Preserve model validation and recovery.
- Retain a paired DOM benchmark report and nine UI correctness checks; reduce simulated preference reads from 373 to 7 per external update and 764 to 26 per edit. This is not a Gecko or whole-browser speed claim; see PERFORMANCE.md.

## Native development validation — 2026-10-18

- Complete the Windows 11 x64 native build, apply the settings/Nimbus integration and pass native defaults/controls/performance checks.
- Fix runtime Quick Suggest regional defaults that re-enabled platform/sponsored suggestions after startup.
- Batch Fluent requests, follow upstream formatting/license conventions, use native design tokens, and document localization variables.
- Diagnose the HTTP mochitest manifest conflict with HTTPS-only navigation and isolate its override to disposable test profiles.

## Lumen Browser branding and QoL — 2026-10-18

- Rename the public product to Lumen Browser, preserving stable internal Lumen/lumen identifiers.
- Add original black/red gear-bezel logo, banner, Windows icons and native installer artwork with a standard-library asset generator.
- Add clear-all filters, Escape reset, scoped slash-to-search and a polite matching count to the settings pane.
- Implement a per-user offline installer with optional shortcuts in a dedicated Start Menu folder, a review summary, `/Help` and `/NoShortcuts` flags, cancellation without a survey, and a foreign-browser destination guard. Disable installer/uninstaller pings and application updates for development builds.
- Compile and visually inspect the native wizard preview; pass 35 refreshed native defaults/identity assertions and 32 controls assertions across both layouts. Verify the final ZIP on a fresh disposable profile.
- Preserve private-window icon distinction and matching upstream optional-icon previews; update native shortcut discovery for the dedicated Start Menu folder.
- Source-build the offline self-extractor with child exit-code propagation; retain resource copyright metadata and deterministic original branding assets.
- Fix omitted resource-generator dependency tracking so incremental module/configuration changes refresh Windows metadata.
- Repeat the final native adapter benchmark: updates 0.844→0.410 ms, edits 1.551→0.611 ms, filtering 0.090→0.023 ms under the documented microbenchmark conditions.

- Verify the exact full unsigned installer: `/Help`, guard exit propagation, shortcut flags/folder, 62 payload hashes, installed icon changes, unchanged defaults and uninstall/profile retention. Artifact hashes and scope are in docs/lumen-artifacts-2026-10-18.json.

## Firefox Release baseline — 2026-10-18

- Apply the owner’s selection of Firefox Release, pinning 158.0 / FIREFOX_158_0_RELEASE / 3c71aeacdb296402e41fb2084b13e797d1770642. Refresh all 91 byte-verified audit snapshots; overlay fixture/model tests pass without removing features. Native Release qualification is in progress; previous artifact and benchmark reports remain identified as 160.0a1 evidence.
