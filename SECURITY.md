# Security policy

No supported Lumen release exists. This source work is experimental and is not recommended for personal browsing. No maintainer contact, private reporting endpoint, or response-time commitment has been supplied. Establish a private vulnerability intake channel before distribution; do not publish exploit details or sensitive profile data in a public report.

For vulnerabilities in upstream Firefox, use [Mozilla's security reporting process](https://www.mozilla.org/en-US/security/). Do not assume Mozilla supports fork-specific changes. Track [Firefox security advisories](https://www.mozilla.org/en-US/security/known-vulnerabilities/firefox/) before each integration/release and regularly during supported operation. No monitoring automation has been configured.

Required process: select an upstream supported baseline, triage advisories, prioritize exploited/critical fixes, stage the new revision, regenerate and review patch differences, compile, run affected suites and packaged network checks, sign artifacts, and publish the exact source/patch provenance. Adopted engineering targets: triage upstream security releases within 24 hours; deliver validated exploited/critical fixes within 72 hours. If safe integration cannot meet that target, stop distributing the affected version and publish accurate status. These targets are not a staffed service guarantee; correctness and validation remain mandatory. See [PRODUCT_GOALS.md](PRODUCT_GOALS.md).

Networking, TLS/certificates, sandbox boundaries, permissions, update signatures, encryption, and profile changes require focused review and failure injection. Never weaken these controls to reduce background traffic. Keep default runtime privilege at standard user and isolate any future elevation to its operation.
