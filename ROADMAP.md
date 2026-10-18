# Roadmap

| Priority | Milestone | State / completion gate |
|---|---|---|
| P0 | Pinned upstream investigation and minimal defaults patch | Implemented; snapshots verified against full checkout and real patch application |
| P0 | Complete network consumer inventory, Glean/DAP/deletion behavior | Preliminary categories documented; source tracing and captures pending |
| P0 | Windows x64 compile and browser integration | Native/frontend builds and extracted ZIP startup succeeded on Windows 11 x64; defaults, both settings layouts and native benchmarks pass |
| P0 | Supported release baseline and security intake | Firefox Release selected; 158.0 source/native/package checks pass; supported product release and security intake remain open |
| P0 | Independent branding/install/profile/update identities | Lumen Browser original branding, separate internal identity and native offline installer implemented; native and full-payload checks pass on Windows 11; signing/updates blocked |
| P0 | Signed updates and recoverable profile migrations | Pending; no infrastructure, keys, or service endpoints supplied |
| P1 | Safe searchable customization/onboarding | 57-control pane, model, import/export and recovery implemented; prior native controls tests pass; refreshed QoL/defaults tests pass and local first-launch controls are verified in the extracted ZIP |
| P1 | Packaged security/network/accessibility/regression matrix | Development binaries exist; complete isolated security/network/accessibility qualification remains pending |
| P1 | Windows 10 and newer x64 compatibility | Required product target; bounded Windows 11 x64 checks pass; Windows 10 and full minimum-API qualification pending |
| P1 | Windows ARM64 | Planned only; no build or support claim |
| P2 | Optional container integration and local usability tools | Evaluate benefits/cost before adding |

No public release date or performance/memory target is promised. Linux/macOS support is outside the initial implementation scope. Upstream services such as push, component downloads, account flows, and AI-related features require individual privacy decisions before product completion.

Follow [DELIVERY_PLAN.md](DELIVERY_PLAN.md) for the applied critical path and [PRODUCT_GOALS.md](PRODUCT_GOALS.md) for accepted quality/security/compatibility requirements. Discretionary feature expansion is deferred until the current build and settings pass their gates.

The source lock now targets Firefox Release 158.0. Source fixture/model checks pass; native Release build/browser/package/installer checks pass on the Windows 11 host. Prior native binaries and performance reports remain 160.0a1 evidence.
