# Fastest maintainable delivery path

The critical path is a working upstream build followed by verified settings integration, packaged privacy/security checks, and fork-safe distribution. Adding another rendering engine, replacing upstream C++, building a separate settings framework, or growing an independent service stack would lengthen that path and increase rebase risk.

## Applied decisions

1. Maintain a small downstream patch repository against an exact Firefox commit instead of duplicating the full upstream tree in this repository. A full pinned checkout and native build live separately under `C:/lumen-work` on the development host.
2. Reuse Firefox's build system, sandbox, native preferences, accessibility, localization, extensions, profile mechanisms and existing tools. Add no new runtime framework or daemon.
3. Generate 57 controls, their localization resources and packaging from one typed catalog. Keep simple and advanced modes in the existing Settings page. Use a pure settings model for fast failure-injection tests without recompiling Gecko.
4. Compile the existing core while completing independent settings tests/documentation. Add frontend changes after that build, then use the upstream frontend rebuild path. Avoid restarting the full compiler for UI-only edits.
5. Run fast tooling/settings tests in Windows/Linux CI on each push/PR. CI does not certify a browser. Full browser, packaging, Windows 10 and privacy checks remain explicit separate gates.
6. Freeze discretionary feature additions until the current build and settings pass their gates. Fix measured usability, compatibility or reliability problems first.

```mermaid
flowchart LR
  A[Pinned source and toolchain] --> B[Native core build]
  C[Catalog and model tests] --> D[Settings integration]
  B --> D
  D --> E[Browser and accessibility tests]
  E --> F[Packaged privacy and recovery checks]
  F --> G[Supported release baseline, branding and signed updates]
  G --> H[Windows 10 and 11 release validation]
```

## Remaining milestones

| Milestone | Exit condition |
|---|---|
| Development build | Successful native x64 compile; real settings pane and defaults verified in Firefox; package created |
| Product integration | Original Lumen branding, separate application/install/profile identity, curated onboarding and accessible settings interactions |
| Privacy and compatibility | Complete source-consumer inventory, packaged traffic evidence, security-preservation tests, extension/accessibility matrix, Windows 10 and Windows 11 execution |
| Release infrastructure | Supported security baseline, private reporting channel, release ownership, signed update identity/service and tested failure recovery |
| Release candidate | Every gate in VERIFICATION.md met; documentation, source provenance and notices match the exact artifact |

No completion date is asserted. Native build success cannot eliminate release infrastructure or test requirements. The current upstream main pin is an investigation/development baseline; the public release needs a supported security-maintained baseline and a fresh validation pass. Read [PRODUCT_GOALS.md](PRODUCT_GOALS.md) for the accepted product requirements and [ROADMAP.md](ROADMAP.md) for scope/status.
