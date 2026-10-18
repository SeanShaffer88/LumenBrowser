# Verification and release gates

## Completed locally

Python tooling validation and unit tests on Windows. The suite verifies snapshot tampering rejection, preference names/types, deterministic patch/source bundle output, bundle manifests, apply/reverse byte restoration against LF fixtures, wrong-revision rejection, protected input preservation, atomic output, and permission-denied/disk-full failure paths. Tests create temporary Git repositories and do not modify global Git settings.

JavaScript model tests cover untrusted/oversized/malformed imports, complete validation before mutation, bounded choices, warnings, dependencies, policy locks, import review, partial-write recovery, failed rollback reporting, failed-reset recovery, privacy-limited exports and unavailable settings. These tests use Node's built-in runner and no external packages. The 57-control browser adapter is a separate integration surface.

All 91 current snapshots match Firefox Release 158.0 commit `3c71aeacdb296402e41fb2084b13e797d1770642`. Native x64 compilation passed on Windows 11 Home build 26300 in 69m 10s. The browser suite passed 68 total checks with no unexpected results; per-test summaries report 35 default passes and 30 controls passes across both layouts. Selected integration lint reports zero errors/warnings/fixes. Each adapter benchmark reported four product assertions. ZIP CRC, fresh-profile launch and full installer flags/payload/shortcuts/registry/uninstall postconditions pass; exact evidence is in [lumen-release-artifacts-2026-10-18.json](lumen-release-artifacts-2026-10-18.json). Earlier 160.0a1 build reports remain historical in BUILD_STATUS.md.

The build is not globally warning-free; SDK/upstream compiler and NSIS warnings are documented. Mochitest uses the HTTP-only disposable-profile override in BUILDING.md; shipped HTTPS-only defaults remain true. Packaged traffic, full accessibility/security/recovery and Windows 10 execution remain unverified.

## Browser integration — partial qualification

1. Follow BUILDING.md with the locked full source, record exact OS, CPU, RAM, toolchain versions, source SHA, configuration, logs, and output hashes.
2. Run generated `browser_lumen_defaults.js` and `browser_lumen_controls.js` in the upstream browser mochitest harness. The controls test exercises both legacy and redesigned preferences. Inspect the preprocessed packaged defaults and `about:buildconfig` separately. Confirm reporting/crash/Nimbus configuration in generated build headers and packaged components; preference presence alone is insufficient.
3. Run upstream suites covering HTTPS exceptions, cookie partitioning, permissions, search suggestions, new-tab lifecycle, telemetry/Glean opt-out and deletion behavior, Remote Settings, extension installation/signing, sandboxing, and certificate failures. Identify exact suite paths in the pinned checkout; do not fabricate successful suite results.
4. Exercise keyboard-only use, screen reader navigation, high contrast, zoom, localization fallback, and extension compatibility. Include settings edits, canceled warnings, parent/child controls, managed policies, search, restore defaults, invalid imports, export scope, actual file dialogs, and unload/observer cleanup. Compare an unmodified same-revision build on the same host for CPU, memory, startup and page performance using PRODUCT_GOALS.md methodology. Store raw measurements. Whole-browser targets and results remain unestablished; bounded settings-adapter measurements are in PERFORMANCE.md.

## Packaged traffic — unverified

Use an isolated Windows test VM with a disposable local profile and no personal data. Capture at the VM gateway or another process-attributed capture layer; browser developer tools alone omit background services. Do not disable TLS verification or add a root certificate to a personal system to inspect traffic.

For both an unmodified baseline package and Lumen package, record process tree, package SHA-256, OS build, DNS/resolver configuration, proxy, locale, region, clock, extensions, and exact action timestamps. Keep raw captures local with access restricted; logs may contain URLs or sensitive data. A capture host OS itself generates traffic: isolate browser traffic through attribution and a control capture.

Test cold first launch, idle periods spanning service timers, restart/shutdown, repeated blank new tabs, typed-but-unsubmitted queries, submitted queries, searches in private windows, permission prompts, safe test downloads, signed extension install/update, connectivity changes, and user-enabled optional services. Trigger telemetry scheduling and crash paths in disposable test environments; absence during a short idle capture proves little. Test fresh and migrated profiles independently once migration exists.

Correlate destination hosts, DNS, connection timing, and encrypted request metadata with source consumers. Exact payloads require instrumented test builds or local controlled endpoints; TLS captures alone do not establish what was transmitted. Unknown traffic fails review. Record each service's trigger, payload fields, control, security trade-off, source trace, and observed result in PRIVACY.md. Retain security-list and certificate functionality checks while auditing telemetry suppression.

Acceptance: no observed nonessential collection requests across the exercised scenarios, no unexplained background requests, source-level upload path review, and preserved security functions. This is bounded evidence, never a proof against all future behavior. Repeat against the exact signed packaged artifact, not only `mach run`.

## Distribution — blocked

- Supported security release baseline and integration process established.
- Lumen branding, application ID, install/profile separation, and name rights reviewed.
- Signed update service, trust roots/channel IDs, failure recovery and interruption tests completed; no signature bypass.
- Fresh install, per-user uninstall, upgrades, rollback using profile backups, disk-full, permission denial and power-loss behavior tested.
- License/notice inventory, source publication, dependency hashes, toolchain provenance and signing process recorded. Reproducibility limitations documented; no reproducible-build claim yet.
- Browser/accessibility/security/network tests pass on every advertised platform; ARM64 requires its own build/run matrix.
- Windows 10 and Windows 11 x64 pass the compatibility matrix in COMPATIBILITY.md; retain the Windows 10 minimum API contract and check the oldest upstream-supported Windows 10 environment.
- Vulnerability reporting contact and supported-version policy published.

No checked tooling test can waive these gates.
