# Windows compatibility contract

Product requirement: **Windows 10 and newer**. Initial architecture: x64. Windows ARM64 is planned separately and must have its own binaries and runtime tests. Tooling checks on an operating system are not browser support certification.

Mozilla's [current Windows build guidance](https://firefox-source-docs.mozilla.org/setup/windows_build.html) lists Windows 10 or later as the build-host baseline. Lumen must retain upstream compatibility paths and avoid adding Windows 11-only imports or APIs. Dynamically resolve newer optional APIs and provide tested Windows 10 fallbacks when adding native code. Do not raise the minimum version as an incidental toolchain or SDK change.

The pinned `build/moz.configure/windows.configure` sets `WINVER` and `_WIN32_WINNT` to `0x0A00`; it is retained in the hash-locked audit snapshots. The current generated build header also preserves this API target. These source/configuration checks support the intended Windows 10 minimum but do not prove runtime compatibility or absence of newer static imports.

| Target | Required release evidence | Current state |
|---|---|---|
| Windows 10 x64 | Clean installation and portable execution, startup, TLS/network, rendering, codecs, sandbox, extensions, accessibility, profile upgrade, update/recovery | Unverified; development x64 binary exists but has not run on Windows 10 |
| Windows 11 x64 | Same functional/security suite on current supported releases | Native build and bounded defaults/settings tests passed on Windows 11 Home build 26300; full release matrix remains unverified |
| Earlier Windows 10 builds | Audit PE/manifest minimum, API availability, runtime dependencies and oldest usable upstream baseline; exercise supported fallback paths | No build-specific compatibility claim established |
| Windows ARM64 | Native build plus the full Windows 10/11 matrix where the OS/architecture combination is supported | Planned only |

Record Windows edition, feature version, build number, architecture, CPU, installed runtime dependencies, exact binary hashes, and test results. A recent Windows 11 host cannot establish Windows 10 compatibility. Include the oldest Windows 10 environment supported by the chosen upstream release in the release matrix; do not silently narrow the user's Windows 10+ requirement to Windows 11 or to the build host.

Security update availability for an OS and API compatibility are different concerns. Do not describe an OS as actively supported by Microsoft without independently verifying that lifecycle policy. The project currently promises neither browser releases nor an OS support service.
