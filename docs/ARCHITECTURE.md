# Scope and architecture decisions

Initial scope: Windows 10 and newer, x64, local development channel, current Firefox main pinned by commit. No public release baseline or support lifecycle has been selected. Main satisfies current-source investigation; a production release must instead pin a supported, security-maintained release and revalidate every patch. Branding is the user-supplied product name Lumen; name clearance, icons, application identity, profile roots, and update identity remain unresolved.

## Dependency sequence

Upstream lock and snapshots -> typed defaults/customization registries -> pure settings model -> existing privileged preferences adapter and Fluent resources -> generated patch -> full upstream build -> packaged behavioral verification -> signing and release.

The patch stays within Mozilla's build and preferences architecture. No wrapper browser, rendering rewrite, profile editor, privileged service, external settings framework, or standalone Rust runtime is introduced. JS and configure Python are the natural integration points; existing Gecko Rust remains intact. Upstream retains process isolation, extension signing, certificate checks, and rendering behavior.

`tools/lumen.py` has no network code and uses Python's standard library. Input snapshot hashes bind patch generation to the audited bytes. Hashes do not prove upstream provenance against a malicious local editor; independently verify the source revision in a real checkout. The optional source preflight checks HEAD and working-tree cleanliness and checks patch applicability. Outputs are atomic per file, not a transaction over a Firefox installation.

## Feature assessment

| Feature | Benefit and privacy impact | Cost/security/upstream fit | Decision |
|---|---|---|---|
| HTTPS-only | Safer navigation; fewer accidental cleartext visits | Some HTTP-only sites need exceptions; existing upstream implementation | Candidate default with upstream exception UI |
| Tracking protection and cookie partitioning | Reduce cross-site correlation while retaining persistent logins | Site regressions possible; use upstream shield and cookie controls | Candidate defaults; per-site tests pending |
| Remote suggestion removal | Avoid transmitting partial queries by default | Less convenience; native search settings preserve control | Candidate defaults |
| Blank new tab | Avoid remote recommendations and promotion surface | Less discovery; small patch but background services need audit | Temporary lean default; polished local page later |
| Searchable settings | Easier discovery, bounded choices and recovery | Existing preferences page, native widgets and Fluent; 57 allowlisted controls | Implemented in source; model tests pass, browser verification pending |
| Containers/private windows | Optional browsing separation | Retain upstream architecture and extension compatibility; cannot imply anonymity | Existing functions retained; integrated container UI evaluation pending |
| Import/export | User ownership and portability | Allowlisted settings only, size/version/type validation, preview and rollback | Settings transfer implemented/model-tested; bookmarks/passwords retain upstream tools |
| AI/sidebar/extra tools | Possible convenience | Remote inference/model downloads and ongoing audit increase scope | No additional implementation; upstream services still need inventory |
| Updates and recovery | Prompt security fixes and recoverability | Highest maintenance cost; independent trust, MAR signing and profile compatibility required | Mandatory before release; not implemented |
| Accessibility/localization | Everyday usability for more users | Preserve Fluent and native browser widgets; regression matrix required | Existing architecture retained; no verified support claim |

## Risks and requirements

The Windows 11 x64 native/frontend builds and bounded defaults/controls/performance browser tests passed. Appending defaults does not remove all callers, telemetry libraries, startup task schedules, or Glean metrics. Disabling the crash reporter needs fault-path validation. Removing build implications needs full compilation and upstream test coverage. User values on an existing profile can override defaults; there is no profile migration yet. Never disable security services merely to satisfy a traffic count target.

Mach's telemetry factory now returns `NoopTelemetry(False)` directly; telemetry enablement returns false and setup returns without employee detection or prompts. This avoids the upstream path that initializes Glean for a deletion ping even when uploads are disabled. It is a scoped build-tool change; browser Glean and other developer utilities remain separate audit surfaces.

The settings adapter runs inside the already-privileged `about:preferences` document. No additional privileged `about:` route or content-to-parent message interface is introduced. Untrusted import data reaches only the validated catalog model; no arbitrary preference names, code, profile paths or external URLs are accepted. Import/reset recovery restores prior preference values and user-branch presence, with an explicit error if rollback itself fails. This is not an on-disk profile migration transaction.

The default pane exposes 33 everyday controls, with 24 less-common or higher-impact controls behind advanced disclosure. No new browser process/service is added. Observer-driven updates run only while the settings document is open, registered observers are tracked for cleanup even after partial initialization, and export object URLs are revoked on replacement or unload. Effective/default preference type disagreement disables a control rather than creating an unsupported value. Write and recovery postconditions are checked before reporting success.

Every release needs independent profile/update identity so Firefox and Lumen cannot update or corrupt each other's installations. Preserve upstream anti-downgrade behavior. Snapshot and recovery validation precede migrations. No high-risk settings will be exposed without documented consequences, validation, dependency controls, and reset behavior.

## Research

Reviewed on 2026-10-18: [Windows setup](https://firefox-source-docs.mozilla.org/setup/windows_build.html), [contributor workflow](https://firefox-source-docs.mozilla.org/contributing/contribution_quickref.html), [telemetry preference/build distinctions](https://firefox-source-docs.mozilla.org/toolkit/components/telemetry/internals/preferences.html), [Remote Settings](https://firefox-source-docs.mozilla.org/services/settings/index.html), and [LibreWolf's feature choices](https://librewolf.net/docs/features/). This is an initial comparator review, not exhaustive fork coverage. Implementation evidence is the hash-locked upstream snapshot set. No benchmark or security assurance is inferred from the research.
