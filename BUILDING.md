# Windows development build

Target: Windows 10 and newer, x64. Current source target: Firefox Release 158.0. The native results below describe the prior 160.0a1 development build until Release qualification completes. The full pinned checkout and isolated MozillaBuild/Rust/compiler environment were prepared under `C:/lumen-work` on the development host; the native x64 build and integrated frontend build succeeded. Native defaults, settings and performance tests passed on Windows 11. Windows 10 remains unverified. The project workspace contains spaces, which upstream does not support for its build paths. Use a separate short source/state path without spaces. Do not change system security settings or existing installations as an incidental build step.

Use the current [Mozilla Windows setup guide](https://firefox-source-docs.mozilla.org/setup/windows_build.html) for supported Visual Studio/SDK, MozillaBuild, Python, Rust, memory, and disk prerequisites. Upstream documents at least 40 GB free disk. Toolchain downloads contact Mozilla and dependency hosts; inspect bootstrap prompts before accepting machine-wide modifications. This repository does not install prerequisites or alter antivirus exclusions.

## Fetch the pinned source

Run in MozillaBuild's shell after preparing prerequisites. Choose a new, empty destination. Fetching only the locked commit avoids downloading years of history. The operation can still transfer substantial data. Local Git config avoids Windows newline conversions and handles long paths without changing global settings. Never substitute a moving branch for the locked revision.

```bash
git init C:/lumen-work/firefox
cd C:/lumen-work/firefox
git config core.autocrlf false
git config core.longpaths true
git remote add origin https://github.com/mozilla-firefox/firefox.git
git fetch --depth=1 origin 3c71aeacdb296402e41fb2084b13e797d1770642
git checkout --detach FETCH_HEAD
```

Apply the patch **before the first Mach invocation** so Lumen's no-op Mach telemetry changes are active. Select a full Firefox desktop build rather than an artifact build because Lumen changes build configuration. Dependency downloads still contact upstream services and need provenance review.

## Prepare and apply

From the Lumen repository in PowerShell, replacing the example path with the actual source path if different:

```powershell
python tools/lumen.py patch --source C:\lumen-work\firefox --output out/lumen.patch
```

This checks the exact commit, requires a clean tree, and runs `git apply --check` before writing the artifact. It does not apply it. Then, in MozillaBuild's shell, set `LUMEN_ROOT` to this repository's actual path; quote it because the path can contain spaces:

```bash
LUMEN_ROOT='/c/path/to/LumenBrowser'
cd C:/lumen-work/firefox
git apply --check "$LUMEN_ROOT/out/lumen.patch"
git apply "$LUMEN_ROOT/out/lumen.patch"
# Copy only if .mozconfig does not already exist. Preserve any existing configuration.
test ! -e .mozconfig && cp "$LUMEN_ROOT/config/mozconfig.windows-x64" .mozconfig
export MOZBUILD_STATE_PATH=C:/lumen-work/state
export CARGO_HOME=C:/lumen-work/cargo
export RUSTUP_HOME=C:/lumen-work/rustup
export DISABLE_TELEMETRY=1
export PATH=/c/lumen-work/cargo/bin:$PATH
./mach --no-interactive bootstrap --application-choice=browser --no-system-changes
./mach build -j8
./mach mochitest --headless --setpref dom.security.https_only_mode=false browser/base/content/test/browser-protectionsUI/browser_lumen_defaults.js
./mach mochitest --headless --setpref dom.security.https_only_mode=false browser/components/preferences/tests/browser_lumen_controls.js
./mach mochitest --headless --setpref dom.security.https_only_mode=false browser/components/preferences/tests/browser_lumen_performance.js
./mach lint browser/components/preferences/lumen.js browser/components/preferences/lumen/settings-model.mjs browser/moz.configure
./mach package
```

Check each command's exit code before the next step. Stop on failure. Do not run build if the copy failed or an existing `.mozconfig` has not been reviewed. The mozconfig is a development candidate, not a validated release configuration. Updater implementation and signature checks remain upstream; fork update identity, endpoints, signing keys, MAR trust, and rollback have not been configured. **Do not distribute this package or permit it to update a personal installation.** The generated overlay replaces unofficial artwork with original Lumen Browser assets and keeps the internal executable name `lumen.exe`. Its development policy disables application updates until a fork update service is qualified; security list consumers remain upstream. See docs/INSTALLER.md for packaging boundaries.

The isolated `CARGO_HOME`/`RUSTUP_HOME` must have rustup and a default stable toolchain before bootstrap. Install rustup from its official distribution with `--no-modify-path --profile minimal --default-toolchain stable`, using those process environment variables; otherwise a global rustup proxy can fail against an empty isolated home. Do not update a user's global Rust installation incidentally. The validated target triple is `x86_64-pc-windows-msvc`; the old `x86_64-pc-mingw32` triple is rejected by this upstream revision.

On the inspected host, MozillaBuild 4.2.1 was extracted from the Mozilla-signed installer rather than executing its installer. Its extracted MSYS2 tree required creating the empty `msys2/tmp` directory. The compiler and SDK were fetched into the local state directory by `--no-system-changes`; no Defender exclusions or global PATH changes were made. Build processes used a minimal allowlisted environment so unrelated application credentials were not passed into compiler subprocesses. Keep raw build logs local: upstream diagnostics can dump environment variables.

For later frontend-only edits after a successful native build, use `./mach build faster` to update packaged UI resources, then rerun affected browser tests. Configuration/native changes require the normal native build. Preserve the actual configure flags, toolchain versions, logs and artifact hashes with each result; do not infer a reproducible build from pinned source alone.

## Run and inspect

Use `./mach run -- -no-remote -profile C:/lumen-test-profile` with a new directory reserved exclusively for disposable testing. Do not import credentials or sign in. Run packaged tests from the packaged executable as well as the build tree; see [VERIFICATION.md](docs/VERIFICATION.md). Do not treat `mach package` success as release approval.

## Reverse source changes

Only in the same checkout, before unrelated edits touch the affected files:

```bash
git apply --reverse --check "$LUMEN_ROOT/out/lumen.patch"
git apply --reverse "$LUMEN_ROOT/out/lumen.patch"
```

Preserve `.mozconfig` and build artifacts separately as needed. Never reset a shared checkout or downgrade an upgraded profile. Restore a verified profile backup to a separate directory for recovery.

The mochitest-only HTTPS preference override is required because the upstream runner fetches its manifest from HTTP on mochi.test. Lumen’s shipped HTTPS-only default otherwise upgrades that request and stalls the harness before assertions. This changes only the disposable test profile; the defaults test still checks the default branch is true. Do not use this override for packaged privacy/network verification.

## Windows self-extractor

The native packager builds a temporary Win32 SFX from the pinned SDK sources so silent setup returns the child installer's actual exit code. The isolated VS/Windows SDK must include Hostx64/x86 compiler/linker tools, x86 libraries and `rc.exe`. Optional build-only overrides are `LUMEN_VS_ROOT` and `LUMEN_WINDOWS_SDK_ROOT`; the default is the isolated `%MOZBUILD_STATE_PATH%\vs` layout. No system PATH or VS installation is modified. See [INSTALLER.md](docs/INSTALLER.md) for exact flags, build compatibility exclusions and test boundaries. Linux tooling CI does not compile this Windows helper.

## Incremental identity/resource changes

Run `./mach configure` after changing `configure.sh` or application display-name configuration before a native build. The inspected upstream resource generator collected `module.ver` dependencies but omitted them from its dependency output; the Lumen overlay records those files and `config/autoconf.mk`, preventing stale public Windows metadata on later incremental builds. Main/private executable metadata overrides append ASCII assignments while retaining upstream legacy-encoded copyright/trademark lines. Verify ProductName, FileDescription and CompanyName on the actual executable, and verify the NSIS stage display name before packaging. A successful unrelated relink alone does not establish refreshed resource metadata.
