# Lumen

Privacy-centric Firefox fork under development. **No supported release exists yet.** This repository maintains the downstream patch set, privacy defaults, a 57-control integrated settings pane, tests, and build/release procedures. It does not establish zero telemetry or production readiness. See [DELIVERY_PLAN.md](DELIVERY_PLAN.md) for the applied completion strategy.

Project repository: [SeanShaffer88/LumenBrowser](https://github.com/SeanShaffer88/LumenBrowser).

[Product goals and release criteria](PRODUCT_GOALS.md): security updates first, measured resource use, simple and advanced settings, Windows 10/11 compatibility and recovery, and verified background-network behavior.

[Current build and verification status](docs/BUILD_STATUS.md) distinguishes completed checks from remaining work. Native Windows 11 x64 builds, default/settings tests, measured settings optimizations, and extracted development ZIP startup have passed. [Artifact evidence](docs/development-artifact-2026-10-18.json) records the exact ZIP hash and limitations.

[Performance investigation](PERFORMANCE.md) records measured bottlenecks, test conditions and the limits of the current evidence.

## Current implementation

- Pinned Mozilla Firefox `160.0a1` development source revision in `upstream.lock.json`; selected source snapshots are hash-verified offline. These snapshots are not a full checkout.
- 31 explained, typed defaults: HTTPS-only navigation, cross-site cookie partitioning, tracking protection, disabled remote search suggestions, disabled new-tab surface, and disabled collection/experiment preferences.
- Generated patch removes application-level Health Reporter and Normandy implications. Development mozconfig disables crash reporting and telemetry reporting, privileged maintenance service, update agent, and default-browser agent. Native compilation succeeded on Windows 11 x64.
- Registered upstream browser mochitest checks default-branch preferences without relying on user preference overrides.
- Integrated Lumen controls in `about:preferences#lumen`: ten categories, search, changed-only filter, advanced disclosure, warnings, dependency checks, policy locks, individual reset, restore defaults, and settings import/export. Native controls tests pass in both Preferences layouts; model failure-injection tests also pass.
- Mach telemetry factory uses the upstream no-op implementation; setup no longer performs employee lookup or opt-in prompts. This source change is tested in isolation; complete build/network behavior still requires verification.
- Nimbus Labs, rollout and study gates are disabled in the patch so the optional experiment loader cannot remain enabled through the Labs policy alone. General Remote Settings security consumers are retained.
- Patch generation never edits the supplied Firefox checkout. Output uses atomic replacement. No package dependencies or runtime services are added.

## Local checks

From this directory, using Python 3.11 or later and Git:

```powershell
python tools/lumen.py validate
python -m unittest discover -s tests -v
node --test tests/settings-model.test.mjs
python tools/lumen.py patch --output out/lumen.patch
python tools/bundle.py --output out/lumen-development-source.zip
```

Tooling validation runs with Python 3.11+ and Git; settings-model tests use Node's built-in test runner (Node 20+). Node is development tooling and adds no browser runtime dependency. Local validation does not certify the Firefox binary. Tool stdout is JSON; errors use stderr and exit code 2. A successful tool command exits 0. The source tools’ `browser_built: false` field describes that invocation only; external native build evidence is recorded separately in BUILD_STATUS.md.

## Scope and installation

Product target: **Windows 10 and newer**, initially x64. The [compatibility matrix](docs/COMPATIBILITY.md) tracks required Windows 10 and Windows 11 verification. Windows 11 x64 development builds and bounded browser tests passed; full release qualification, Windows 10, ARM64, Linux and macOS remain unverified. Packaging still uses upstream development identity. Follow [BUILDING.md](BUILDING.md) for an isolated development build. Do not use personal browsing profiles with experimental builds.

Firefox's existing settings, accessibility architecture, WebExtensions, bookmark tools, password tools, and rendering engine remain the foundation. The Lumen pane is implemented but not yet verified in a running browser. Onboarding, profile migration, original branding assets, and fork updates are not implemented. New Rust components are not introduced merely to satisfy a language preference; use the language that fits each upstream boundary.

## Documentation

[Privacy and connections](PRIVACY.md) · [Architecture and feature decisions](docs/ARCHITECTURE.md) · [Windows compatibility](docs/COMPATIBILITY.md) · [Build](BUILDING.md) · [Customization and recovery](docs/CUSTOMIZATION.md) · [Verification](docs/VERIFICATION.md) · [Security](SECURITY.md) · [Roadmap](ROADMAP.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md)

New project code is MPL-2.0; upstream files retain their notices. See [LICENSE](LICENSE) and [CREDITS.md](CREDITS.md). No registration, ads, licensing service, or telemetry is added by the local tooling. The browser's complete privacy behavior remains a release gate.
