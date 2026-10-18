# Product goals and acceptance criteria

These requirements implement the project owner's accepted goal adjustments. They are development/release criteria, not claims of completed verification.

## 1. Security updates take precedence

Use the owner-selected **Firefox Release** channel, pinned to an exact stable release revision, and qualify each security-maintained baseline before public distribution. Keep the downstream patch set small enough to rebase routinely. Target triage within 24 hours of an upstream security release and delivery of a validated fix within 72 hours for exploited or critical issues. These are engineering targets, not a staffed service guarantee. If a safe integration cannot meet the target, stop distributing the affected build, document the gap, and prioritize the fix over new features. Do not ship an unvalidated update to satisfy a clock.

A private reporting channel, release owner, supported-version list, signing keys, and update infrastructure are required before launch. No monitoring automation or maintainer availability is implied by this policy.

## 2. Measure lightweight behavior

Compare Lumen and an unmodified same-revision Firefox build on the same Windows hardware, OS, toolchain, build mode and representative profiles. Record cold/warm startup, idle CPU, private/working-set memory, tab workloads, and page responsiveness. Use repeated runs, document caching and network conditions, retain raw results, and report variation. Establish budgets from that baseline before setting numerical performance limits.

Investigate repeatable regressions beyond observed measurement variability. Do not accept a feature merely for its count when it increases background work, memory, dependencies or maintenance without a clear user benefit. Idle work should be event-driven; add no unbounded polling or optional background daemon. Settings-layer improvements are measured in native Gecko; whole-browser resource/startup advantages remain unmeasured.

## 3. Simple primary interface, searchable advanced controls

Expose common tasks using existing Firefox navigation and accessible widgets. Keep advanced options behind disclosure while preserving search by ordinary language and preference name. Explain consequences beside each setting, show the shipped default, validate values, respect policy locks and feature dependencies, and provide individual reset plus confirmed restore defaults.

Import/export covers only the curated settings schema; it must not include passwords, cookies, browsing history or arbitrary profile data. Validate the full import before mutation and restore previous preference values if a multi-setting operation fails. Test invalid files, unavailable settings, policy locks and rollback failure. Do not expose sandbox, certificate, extension-signing or update-signature bypasses.

## 4. Compatibility and recovery are release gates

Target Windows 10 and newer, initially x64. Run the matrix in [COMPATIBILITY.md](docs/COMPATIBILITY.md) on Windows 10 and Windows 11; include the oldest Windows 10 environment supported by the chosen upstream baseline. Test common extensions, keyboard navigation, screen readers, high contrast, display scaling, fresh installation, upgrades and profile recovery. ARM64 requires independent native testing before a support claim.

Never migrate a running profile or silently downgrade an upgraded profile. Use verified backups, staged operations and failure-injection tests for migrations and updates. A passing Windows 11 build cannot substitute for Windows 10 execution.

## 5. Predictable, demonstrable privacy

Maintain a source-backed inventory of every background service, trigger, transmitted data category, default, user control and security trade-off. Remove nonessential collection without weakening certificate validation, sandboxing, security lists or extension signatures. Separate build-tool telemetry from browser telemetry in the audit.

Execute the [packaged traffic procedure](docs/VERIFICATION.md) on the exact release artifact, including first launch, idle, shutdown, opt-in features and update paths. Investigate unknown connections and retain sanitized evidence. No zero-telemetry, anonymity, universal security or best-browser claim is permitted without bounded supporting evidence.

## Feature selection

Favor upstream capabilities and small integrations. For each addition document usefulness, privacy, performance, maintenance, security and compatibility. Prefer one coherent implementation per task. Defer speculative additions that would crowd navigation or delay these five gates. Polish means predictable interactions, accessible feedback, sensible defaults and reliable recovery, not animation or decorative assets that add overhead.
