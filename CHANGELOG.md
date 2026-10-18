# Changelog

## Unreleased — development foundation, 2026-10-18

- Integrate into SeanShaffer88/LumenBrowser while preserving the existing MPL-2.0 license.
- Establish Windows 10 and newer as the compatibility target, with a dedicated release matrix.
- Add Windows/Linux foundation CI and deterministic source bundles with SHA-256 inventories; CI does not build a browser.
- Add an integrated 57-control settings pane with search, categories, advanced disclosure, reset, policy/dependency guards, and validated settings import/export with rollback handling.
- Disable Mach telemetry initialization and setup through the upstream no-op implementation; browser telemetry remains separately unverified.
- Prepare a full pinned source checkout and isolated MozillaBuild/Rust/compiler environment; native build is in progress.
- Adopt product quality gates and a documented critical path that prioritizes build verification over further discretionary features.

- Pin Firefox main revision `4523d65b575546e2b588dfb8b91e3d94ebeec19a` (`160.0a1`) with selected hash-verified source snapshots.
- Add 31 explained privacy/security default preferences and a deterministic source patch generator.
- Generate Health Reporter/Normandy configure changes and a registered browser default-preference test.
- Add candidate Windows x64 full-build configuration, privacy inventory, failure-injection tooling tests, and release procedures.
- No binary, installer, browser test result, complete telemetry-removal guarantee, finished branding, update service, migration implementation, or supported platform release.
