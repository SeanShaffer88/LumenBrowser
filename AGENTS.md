# Lumen development instructions

LumenBrowser is a downstream Firefox patch repository. The product target is Windows 10 and newer, initially x64. Preserve the existing MPL-2.0 license and upstream notices. Do not claim a supported release, runtime compatibility, privacy guarantee or benchmark result without performed verification.

Read PRODUCT_GOALS.md, DELIVERY_PLAN.md and docs/BUILD_STATUS.md before choosing work. Prioritize a working verified browser and release gates over discretionary feature growth. Reuse upstream boundaries: Rust where appropriate for native components, JavaScript/Fluent for preferences, and Mozilla's existing build/test infrastructure.

Dependency sequence: upstream lock/snapshots -> typed defaults/customization catalogs -> settings model -> privileged preferences adapter -> generated patch -> upstream build -> packaged verification. Snapshots under audit/upstream are reference bytes; change them only as an explicit audited pin/snapshot update and update upstream.lock.json hashes. Preserve snapshot bytes in Git.

Required local checks for relevant code changes:

```text
python tools/lumen.py validate
python -m unittest discover -s tests -v
node --test tests/settings-model.test.mjs
python tools/lumen.py patch --output out/lumen.patch
python tools/bundle.py --output out/lumen-development-source.zip
```

Tooling/model CI is not a Firefox build or browser test. Run the registered upstream mochitests and applicable native lint/build checks for browser changes. Keep browser/UI/accessibility/Windows 10/network verification separate in status reports. Test actual postconditions and failed recovery; never report a failed rollback as successful restoration.

Keep controls allowlisted and bounded. Respect policy locks, dependencies, warning confirmation and reset recovery. No sandbox/certificate/signature bypass controls. Import/export must never include arbitrary profile preferences or personal browsing data. Retain event-driven updates and remove observers/object URLs on unload.

Keep source/build/state paths free of spaces. Use isolated build caches/toolchains and --no-system-changes. Do not alter global PATH, user Rust installations, antivirus settings or personal profiles incidentally. Forward only required environment variables to build tools; raw diagnostics may dump the environment. Keep raw logs/captures and generated artifacts outside Git under ignored output paths or the dedicated development directory. No profile/capture uploads in CI.

The enclosing Meridian repository and synced sources/ material are unrelated and must not be modified. Follow any additional instructions in the real upstream Firefox checkout when working there. Preserve in-progress native build artifacts; frontend-only changes should use the upstream frontend rebuild path after the native build completes.
