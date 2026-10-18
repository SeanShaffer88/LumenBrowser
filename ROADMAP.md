# Roadmap

| Priority | Milestone | State / completion gate |
|---|---|---|
| P0 | Pinned upstream investigation and minimal defaults patch | Implemented; snapshots verified against full checkout and real patch application |
| P0 | Complete network consumer inventory, Glean/DAP/deletion behavior | Preliminary categories documented; source tracing and captures pending |
| P0 | Windows x64 compile and browser integration | Native/frontend builds and extracted ZIP startup succeeded on Windows 11 x64; defaults, both settings layouts and native benchmarks pass |
| P0 | Supported release baseline and security intake | Not selected/published; main pin is development only |
| P0 | Independent branding/install/profile/update identities | Pending; development assets must not ship as finished Lumen |
| P0 | Signed updates and recoverable profile migrations | Pending; no infrastructure, keys, or service endpoints supplied |
| P1 | Safe searchable customization/onboarding | 57-control pane, model, import/export and recovery implemented; browser verification and onboarding pending |
| P1 | Packaged security/network/accessibility/regression matrix | Pending real binaries and isolated test environment |
| P1 | Windows 10 and newer x64 compatibility | Required product target; Windows 10/11 runtime and minimum-API checks pending |
| P1 | Windows ARM64 | Planned only; no build or support claim |
| P2 | Optional container integration and local usability tools | Evaluate benefits/cost before adding |

No public release date or performance/memory target is promised. Linux/macOS support is outside the initial implementation scope. Upstream services such as push, component downloads, account flows, and AI-related features require individual privacy decisions before product completion.

Follow [DELIVERY_PLAN.md](DELIVERY_PLAN.md) for the applied critical path and [PRODUCT_GOALS.md](PRODUCT_GOALS.md) for accepted quality/security/compatibility requirements. Discretionary feature expansion is deferred until the current build and settings pass their gates.
