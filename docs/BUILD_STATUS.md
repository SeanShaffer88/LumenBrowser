# Development verification status — 2026-10-18

This document records performed work and explicitly separates it from release requirements. It is not a release announcement.

| Check | Evidence / state |
|---|---|
| Project repository | SeanShaffer88/LumenBrowser; original main license preserved |
| Upstream | Full checkout of `4523d65b575546e2b588dfb8b91e3d94ebeec19a`, version `160.0a1` |
| Snapshot provenance check | Imported audit snapshots compared against bytes in the real pinned checkout |
| Real patch check | Defaults/configure/Mach telemetry patch checked and applied to the full checkout |
| Settings patch | Implemented; generated full patch applies/reverses in exact-file fixtures; full-tree application after ongoing build remains pending |
| Tooling tests | 13 Python tests passed locally |
| Settings model tests | 9 Node tests passed locally; no npm dependencies |
| Source packaging | Deterministic archive generation, ZIP integrity and complete SHA-256 manifest tested |
| Development host | Windows 11 Home x64, build 26300; not a Windows 10 test environment |
| MozillaBuild | 4.2.1, extracted locally from a Mozilla-signed installer; installer not executed |
| Build Python / Rust | MozillaBuild Python 3.12.10 / isolated Rust 1.99.1 |
| Toolchain bootstrap | Completed with `--no-system-changes`; compiler/SDK/state under the dedicated development directory |
| Build target | `x86_64-pc-windows-msvc`; generated `WINVER` and `_WIN32_WINNT` remain `0x0A00` |
| Native compilation | In progress, eight workers; no successful browser artifact yet |
| Browser mochitests | Implemented/registered; not yet executed |
| UI visual/accessibility checks | Pending real browser execution |
| Windows 10 runtime | Unverified |
| Packaged network/privacy behavior | Unverified; no zero-telemetry claim |
| Fork release identity/signing/updates | Not configured; distribution blocked |

The host uses a separate source/state directory without spaces. Build subprocesses receive an allowlisted environment; personal application credentials are not intentionally forwarded. Raw toolchain/build logs remain local and are not included in the source bundle or GitHub CI artifacts. The build candidate retains upstream security mechanisms and uses nonofficial development branding. Full release gates are in [VERIFICATION.md](VERIFICATION.md), with the work order in [DELIVERY_PLAN.md](../DELIVERY_PLAN.md).
