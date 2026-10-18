# Lumen Browser development installation

No supported or signed release exists. The final native Windows ZIP and full offline self-extracting installer were built and tested on Windows 11 x64. `/Help`, exit-code propagation, foreign-browser rejection, a path containing spaces, `/NoShortcuts`, 61 payload hashes, repeat installation, both shortcut locations, custom-icon selection/revert, default-choice preservation and uninstall/profile retention passed. [Exact artifacts and evidence](lumen-release-artifacts-2026-10-18.json) identify the build. UI-only previews were canceled before installation; their visual checks are separate from the final silent full-payload tests. Failed/interrupted upgrades, protected destinations, Windows 10 and complete accessibility/network qualification remain open.

## Identity and visual design

The public product name is **Lumen Browser**. Stable implementation identifiers are `Lumen` (application/vendor), `lumen` (remoting/application name), and `lumen.exe`. Keeping these names avoids unnecessary profile and registry churn when the public label changes. The Firefox application GUID is retained for existing extension and automation compatibility; it is not a claim of Mozilla branding. The application uses its own Lumen/Lumen application-data hierarchy and a separate installation folder. No Firefox profile migration is implemented.

Original black/charcoal artwork uses a red gear-like bezel, pale monogram and restrained rivets. `branding/lumen.svg` is the scalable source; `tools/make_branding.py` reproducibly creates the raster icon sizes and installer watermarks using only Python’s standard library. Small icons omit tiny rivets. ICO frames use legacy-compatible DIB images at 16/32/48 pixels and PNG at 256 pixels. Native wizard widgets retain Windows behavior and accessibility rather than adding a UI runtime. Header artwork has a separate right-to-left placement.

## Installer behavior

The interactive flow is Welcome → Location → Shortcuts → Review → Install → Finish. The default location is `%LOCALAPPDATA%\Lumen Browser`, so a standard per-user installation does not request elevation. An explicitly protected custom destination may invoke the existing upstream permission path; that path is not yet qualified. Start-menu shortcuts are selected by default; desktop/taskbar additions are opt-in and taskbar availability follows upstream Windows capability checks. Review lists the selected shortcuts. Cancellation uses a simple confirmation without an exit survey.

A destination containing `firefox.exe`, `chrome.exe` or `msedge.exe` is rejected before installation, including silent mode, with exit code 2. This guard is intentionally limited: it cannot identify every third-party application or eliminate filesystem races. Choose a dedicated empty folder. Existing upstream disk-space, file-in-use and permission checks remain in place. Installer/uninstaller pings and installation telemetry writing are disabled in the overlay. Uninstallation keeps the separate browsing profile and offers no survey. These are source behaviors requiring actual payload/recovery validation, not a complete atomic installer guarantee.

The build disables the maintenance service, background update agent and default-browser agent. The packaged `distribution/policies.json` sets `DisableAppUpdate` and `DontCheckDefaultBrowser`. The initial welcome page opens local `about:preferences#lumen` instead of a network onboarding page. The browser is not automatically made the default. Disabling application updates does **not** make an experimental browser safe for ongoing use; signed, authenticated and recoverable fork updates are a public-release gate. General Remote Settings and security protections are not disabled by this packaging policy.

## Build and verification

Generate and apply the pinned overlay as described in [BUILDING.md](../BUILDING.md), then run `mach package` on native Windows. This builds the ZIP and offline self-extracting installer using upstream tooling. The packaging action compiles the pinned upstream Win32 SFX sources in a temporary directory with a small child-exit-code fix, then brands icon/version resources before UPX compression. It refuses a signed source SFX and preserves original copyright text. No third-party Python package or browser runtime is introduced. Cross-compiling this resource action from Linux is unsupported.

Required checks include archive CRC and policy presence; fresh-profile launch from the extracted ZIP; silent installation in an owned path containing spaces; foreign-browser sentinel rejection; shortcut choices; default-browser state preservation; version/icon identity; removal of the test installation while retaining profile data; failed/interrupted upgrade recovery; and standard-user Windows 10/11, scaling, keyboard and screen-reader execution. Signing, all-users/elevation, ARM64 and whole-application network qualification remain open. Raw logs and test profiles stay local.

For NSIS command-line execution, quote the destination **value**, for example `/InstallDirectoryPath="C:\owned test folder\Lumen"`, rather than quoting the entire `/InstallDirectoryPath=...` argument. A local Python `subprocess` list automatically quoted the whole argument and did not exercise the intended destination; the corrected native command line passed the sentinel test. Do not infer success from exit 0 alone: verify installed files and policy/profile behavior. Test with `/S /DesktopShortcut=false /StartMenuShortcut=false /TaskbarShortcut=false /MaintenanceService=false /RegisterDefaultAgent=false` in a dedicated owned directory.

## Command-line options

| Flag | Behavior |
|---|---|
| `/S` | Install silently; verify the exit code and installed files. |
| `/InstallDirectoryPath="C:\owned folder\Lumen Browser"` | Choose a dedicated destination; quote the value separately. A valid destination option also selects silent mode upstream. |
| `/DesktopShortcut=true` or `false` | Create or omit the desktop shortcut; default false. |
| `/StartMenuShortcut=true` or `false` | Create or omit `Lumen Browser\Lumen Browser.lnk` in the Start Menu; default true. |
| `/TaskbarShortcut=true` or `false` | Request or omit a taskbar pin where Windows supports it; default false. |
| `/PrivateBrowsingShortcut=true` or `false` | Create or omit an additional private-window shortcut in the same Start Menu folder; default false. |
| `/NoShortcuts` | Override individual choices: no desktop, Start Menu, private-window shortcuts or taskbar pin. Interactive users can subsequently change wizard choices. |
| `/Help` | Show supported install flags and exit before destination setup. Combine with `/S` for a noninteractive help-exit check (passed without creating the supplied destination). |

The visible shortcut choices are **Create Desktop Shortcut** and **Create Start Menu Shortcut**. Desktop is unchecked and Start Menu is checked by default. All Start Menu links created by this overlay use their own **Lumen Browser** folder; removal deletes that folder only if empty. Existing upstream `/INI=` configuration remains available for advanced deployment, but INI/elevated paths are not yet qualified here. Maintenance-service/default-agent flags do not enable components excluded at build time. No licensing, registration or updater bypass flags are provided.

## Test harness boundaries

Mochitest redirects `MOZ_APP_DATA`/`MOZ_LOCAL_APP_DATA` to temporary AppData roots, and Nightly ignores local policies when `Cu.isInAutomation` is true. Those harness settings cannot prove the shipped profile hierarchy or distribution policy. Direct fresh-profile startup instead launches the owned binary as a subprocess, attaches Marionette, leaves those directory overrides unset and keeps `remote.prefs.recommended=false` in the disposable test profile. The latter prevents automation from replacing the welcome URL with `about:blank`. That direct run confirmed Lumen/Lumen application-data leaf names, `DisableAppUpdate`, the public controls title and a first local tab at `about:preferences#lumen`. These test-only automation settings are not shipped browser defaults.

The development policy uses Firefox's standard enterprise-policy mechanism and therefore displays its standard “managed by your organization” Settings banner. This is a known development UI limitation; it does not indicate a remote management service added by Lumen Browser. A supported update implementation and its release UX remain unfinished.

## Self-extractor exit-code correction

The original upstream SFX waited for its setup child and always returned 0. A controlled child that exited 37 reproduced outer exit 0; the patched source returned 37 with the same child payload. The fix waits for completion, retrieves the child exit code, closes its process handle on success/error paths and returns Windows error 1603 if waiting/querying fails. Decoder logic is unchanged. The final full payload test confirms that the foreign-browser guard’s exit 2 reaches the caller.

`tools/sfx_builder.py` compiles the 82 units listed by the pinned upstream Visual Studio project using eight bounded workers, static CRT, `/GS`, `/DYNAMICBASE`, `/NXCOMPAT`, `/SAFESEH` and Windows 10 target declarations. No precompiled replacement or new runtime is added. Compilation preserves warnings-as-errors; only modern MSVC warning C5286 is excluded for the two unchanged legacy LZMA2 decoder C files. This compatibility exclusion leaves their existing enum conversions unchanged and requires review on an SDK/compiler update.

The build requires local MSVC Hostx64/x86 tools, x86 VC/UCRT/Windows libraries and the SDK resource compiler. The existing isolated Mozilla bootstrap provides these on the verified host. `LUMEN_VS_ROOT` and `LUMEN_WINDOWS_SDK_ROOT` can specify explicit roots; otherwise the helper uses `VSINSTALLDIR`/`WindowsSdkDir` or `%MOZBUILD_STATE_PATH%\vs`. Versioned tool directories are selected numerically. Build subprocesses receive a minimal environment, each invocation has a timeout, and all files are compiled under the packager's temporary directory. Native Windows x64 packaging is verified independently of any future ARM64 qualification.

[Recorded component-probe evidence](installer-probe-2026-10-18.json) distinguishes these checks from the final packaged-artifact pass. The first uninstall check stopped as soon as the main executable disappeared and raced later file deletion; the corrected check waits for both core files and owned shortcuts before asserting completion.

Native custom-icon discovery now includes the dedicated Start Menu folder while preserving legacy root-link discovery and existing executable/AUMID ownership checks. The default/private artwork is original Lumen design; optional upstream icon resources retain their matching previews. Windows metadata uses Lumen Browser/Lumen Project and preserves upstream notices.

The current tested source baseline is Firefox Release 158.0. Windows Installed Apps displays Lumen Browser (x64 en-US); the internal registry key remains stable, and the owned uninstall entry is verified removed. Previous 160.0a1 artifacts and the component probe remain historical. The current installer is unsigned and is not a supported Lumen release.
