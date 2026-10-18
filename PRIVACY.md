# Privacy status and initial network inventory

**No packaged Lumen browser has been executed or captured. Zero telemetry is not established.** The table is a preliminary inventory of Firefox service classes, not an exhaustive endpoint or code-path audit. Transmitted fields below describe expected categories; payload schemas, timing, and regional variants need pinned-source tracing and runtime confirmation. Every remote service sees some network metadata, usually the connecting IP and request timing.

The source patch sets defaults; existing profile values, policies, experiments, extensions, or future upstream code can override behavior. Development compilation flags are not yet proven effective. Legacy telemetry and Glean are separate audit surfaces ([Mozilla telemetry documentation](https://firefox-source-docs.mozilla.org/toolkit/components/telemetry/)).

| Connection / classification | Trigger and potentially transmitted information | Lumen candidate default / control | Disabling trade-off and evidence gap |
|---|---|---|---|
| Legacy telemetry / nonessential | Startup, periodic, shutdown; measurements, environment, identifiers depending on ping | Upload/unified/archive/ping defaults off; reporting build env unset | Diagnostics unavailable; all scheduling and deletion-ping paths unverified |
| Glean and DAP / nonessential | Feature metrics, ping scheduling; payload varies by metric | Upload master preference off; characteristics opt-out true | Exact upload gating, local collection, DAP and deletion requests require audit |
| Crash submission / optional | Crash and submit action; memory dump may contain sensitive data | Crash reporter disabled in build candidate | Remote crash diagnosis unavailable; package must prove component absence |
| Normandy and Nimbus / nonessential experiments | Startup/refresh; experiment metadata and targeting | Normandy implication removed; runner/targeting defaults off; Labs/rollout/study source gates return false | New experiments unavailable; remote loader enablement path traced; packaged absence still needs capture |
| New-tab content, advertising, measurement / nonessential | Opening new tab, content refresh; contextual or interaction data | New-tab surface and private ping default off | Blank new-tab experience; background fetches need independent verification |
| Search suggestions / optional | Typing; partial query sent to selected search provider | Suggestions off in search and URL bar; Settings > Search | No remote completions; user-submitted searches still contact engine |
| Firefox Suggest / optional | Typing; contextual query data depending on implementation | Quick Suggest and sponsored/nonsponsored suggestion defaults off | Fewer suggestions; ingestion and regional configuration unverified |
| Add-on discovery / optional | Opening add-ons UI; browser/version and recommendation context | Discovery and HTML recommendation defaults off | No personalized discovery; AMO navigation still user-initiated |
| Extension updates / security maintenance | Periodic checks after add-on installation; add-on IDs/version/platform | Retained upstream; add-on update controls | Disabling can retain vulnerable extensions; request payload and cadence pending |
| System add-on updates / maintenance | Periodic; build/platform details | Retained upstream, pending service-level audit | Blind removal could remove fixes; release requires fork-safe identity review |
| Safe Browsing / security | List refresh, reputation checks/download checks; list state and lookup information | Retained upstream; security settings | Disabling reduces malware/phishing defense; exact remote lookup disclosure pending |
| Remote Settings / security and mixed purposes | Poll/sync; collection/version and application metadata | Retained; audit collections individually | Blanket disabling can lose blocklist/security changes; nonessential consumers need removal |
| Certificates / security | TLS handshakes, revocation/intermediate retrieval as configured; certificate-related information | Retained upstream | Disabling can weaken validation or cause failures; OCSP/CRLite behavior pending |
| Application updates / security maintenance | Scheduled/manual; version/build/OS/channel metadata | Updater retained; no Lumen service deployed | Fork identity/trust not configured: distribution blocked, no automatic-update guarantee |
| Account and Sync / user-initiated | Sign-in and synchronization; account metadata and encrypted sync records | Upstream available; no sign-in by default; two account telemetry defaults off | No sync if unused/disabled; account flows remain unverified |
| DNS and DNS-over-HTTPS / functional and optional | Navigation, resolver selection and service heuristics; names and network metadata | Upstream resolver behavior retained; DNS prefetch off | Resolver changes can cause availability/security trade-offs; rollout/heuristic traffic pending |
| Captive portal and connectivity / functional | Network changes/startup; connectivity probe metadata | Upstream retained pending audit | Disabling can break Wi-Fi login discovery; exact probes need tracing |
| Push / optional website feature | Push service connection and subscribed notification delivery; subscription metadata | Upstream retained; site permission controls | Disabling breaks web push; idle connection pending audit |
| Geolocation / permission-gated | User-approved site request; location/network signals per provider | Upstream permission gate retained | Disabling prevents location features; payload and platform provider pending |
| Translation, DRM, model/component downloads / optional | Feature use, component checking; locale/component/version metadata | No Lumen bundling; upstream behavior pending audit | Disabling breaks the relevant feature; background downloads need verification |
| Visited sites and submitted searches / user-initiated | Navigation/search; URLs, content requests, cookies per policy | Required for ordinary browsing; site controls | Browser privacy settings cannot anonymize traffic from destination services |
| Build dependencies / development | Source clone, bootstrap, toolchain download; network metadata | Explicit developer operation; local validator/generator are offline; patched Mach uses no-op telemetry | Other developer tools/transitive downloads remain separate audit surfaces; full network capture pending |

Remote Settings includes security consumers; its removal is not a substitute for identifying nonessential consumers ([upstream service documentation](https://firefox-source-docs.mozilla.org/services/settings/index.html)). Unlike [LibreWolf's documented Safe Browsing choice](https://librewolf.net/docs/features/), Lumen's candidate retains that security mechanism. This comparison is limited to that published design choice.

Pinned-source tracing found that `ExperimentAPI.labsEnabled` depended on enterprise policy allowance, independently of the studies/upload preferences. `RemoteSettingsExperimentLoader.enable()` checks `ExperimentAPI.enabled`, which is the union of Labs/rollout/study gates. The patch disables those three optional experiment gates explicitly rather than disabling Remote Settings as a whole. A generated browser test checks the resulting disabled state; execution is pending. Browser Glean remains compiled and must be audited separately; disabled upload defaults and build reporting flags are not proof that all measurement code is absent.

## Local data

Tooling reads repository snapshots and configuration and writes only its requested patch artifact. It does not inspect browser profiles or send network requests. Audit snapshots were downloaded during project creation, and upstream metadata lookup contacted GitHub. No user credentials, browser data, or crash dumps were used.

The browser retains upstream profile storage, password encryption, cookie storage, and history semantics pending review. Private browsing does not provide anonymity or guaranteed forensic erasure. Extension privacy behavior is outside the scope of these default preferences. Password CSV exports are plaintext: use upstream's explicit warning and avoid exporting for tests.

The implemented settings editor exports only values from its 57-entry allowlist. It cannot export arbitrary profile preferences, passwords, cookies, history, bookmarks or file paths. Import is local, versioned and size-bounded; it previews changes and warnings and respects policy locks. Unsupported custom values are reported as omitted during export. Browser execution of these flows remains unverified even though the independent model tests cover validation and recovery.

## Required proof

Complete the [verification procedure](docs/VERIFICATION.md), attach sanitized captures and exact build hashes, classify every unexpected connection, and close all release gates before strengthening these claims. Record source and packaged behavior separately.
