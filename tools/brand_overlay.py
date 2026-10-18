"""MPL-2.0. Small, audited Lumen branding and native offline installer overlay."""

from functools import lru_cache
from pathlib import Path
import re
import subprocess
import tempfile

BASE = "browser/branding/unofficial/"
REPO = "https://github.com/SeanShaffer88/LumenBrowser"
HEADER = "# This Source Code Form is subject to the terms of the Mozilla Public\n# License, v. 2.0. If a copy of the MPL was not distributed with this\n# file, You can obtain one at http://mozilla.org/MPL/2.0/.\n\n"
BINARY = {
    "toolkit/mozapps/installer/windows/nsis/setup.ico": "lumen.ico",
    **{
        BASE + f"default{s}.png": f"logo-{s}.png"
        for s in (16, 22, 24, 32, 48, 64, 128, 256)
    },
    **{
        BASE + name: "lumen.ico"
        for name in (
            "firefox.ico",
            "firefox64.ico",
            "document.ico",
            "document_pdf.ico",
            "newtab.ico",
            "newwindow.ico",
            "pbmode.ico",
        )
    },
    BASE + "wizHeader.bmp": "header.bmp",
    BASE + "wizHeaderRTL.bmp": "header-rtl.bmp",
    BASE + "wizWatermark.bmp": "wizard.bmp",
    **{
        BASE + name: f"logo-{size}.png"
        for name, size in (
            ("VisualElements_70.png", 70),
            ("VisualElements_150.png", 150),
            ("PrivateBrowsing_70.png", 70),
            ("PrivateBrowsing_150.png", 150),
        )
    },
    **{
        BASE + "content/" + name: f"logo-{size}.png"
        for name, size in (
            ("about.png", 256),
            ("about-logo.png", 128),
            ("about-logo@2x.png", 256),
            ("about-logo-private.png", 128),
            ("about-logo-private@2x.png", 256),
        )
    },
}
BINARY[BASE + "pbmode.ico"] = "lumen-private.ico"
for name, size in (
    ("PrivateBrowsing_70.png", 70),
    ("PrivateBrowsing_150.png", 150),
    ("content/about-logo-private.png", 128),
    ("content/about-logo-private@2x.png", 256),
):
    BINARY[BASE + name] = f"logo-private-{size}.png"

TEXT = [
    BASE + path
    for path in (
        "configure.sh",
        "branding.nsi",
        "locales/en-US/brand.ftl",
        "locales/en-US/brand.properties",
        "pref/firefox-branding.js",
        "content/about-logo.svg",
        "content/about-wordmark.svg",
        "content/firefox-wordmark.svg",
        "content/document_pdf.svg",
        "firefox.VisualElementsManifest.xml",
        "private_browsing.VisualElementsManifest.xml",
    )
]
TEXT += [
    "browser/branding/branding-common.mozbuild",
    "browser/app/moz.build",
    "browser/installer/windows/nsis/defines.nsi.in",
    "browser/installer/windows/nsis/installer.nsi",
    "browser/installer/windows/nsis/uninstaller.nsi",
    "browser/installer/windows/nsis/install_dir_helpers.nsh",
    "toolkit/mozapps/installer/windows/nsis/common.nsh",
    "browser/locales/en-US/installer/mui.properties",
    "browser/locales/en-US/installer/custom.properties",
]


def once(text, before, after):
    if text.count(before) != 1:
        raise ValueError(f"Branding boundary mismatch: {before[:70]}")
    return text.replace(before, after, 1)


def nsis_function(text, name, body):
    pattern = rf"^Function {re.escape(name)}\n.*?^FunctionEnd\n"
    text, count = re.subn(
        pattern,
        lambda _: f"Function {name}\n{body}FunctionEnd\n",
        text,
        flags=re.M | re.S,
    )
    if count != 1:
        raise ValueError(f"Missing or duplicate NSIS function: {name}")
    return text


def start_menu_folder(text):
    for name in (
        "${BrandShortName}.lnk",
        "${BrandFullName}.lnk",
        "$(PRIVATE_BROWSING_SHORTCUT_TITLE).lnk",
    ):
        text = text.replace(
            "$SMPROGRAMS\\" + name, "$SMPROGRAMS\\Lumen Browser\\" + name
        )
        text = text.replace(
            '${LogStartMenuShortcut} "' + name + '"',
            '${LogStartMenuShortcut} "Lumen Browser\\' + name + '"',
        )
    text = re.sub(
        r'^(\s*)(CreateShortCut|CreateShortcut)( "\$SMPROGRAMS\\Lumen Browser\\)',
        lambda m: (
            m[1] + 'CreateDirectory "$SMPROGRAMS\\Lumen Browser"\n' + m[1] + m[2] + m[3]
        ),
        text,
        flags=re.M,
    )
    return text


@lru_cache(maxsize=64)
def binary_diff(path, before, after):
    if before == after:
        return ""
    with tempfile.TemporaryDirectory(prefix="lumen-brand-") as directory:
        left, right = Path(directory) / "before", Path(directory) / "after"
        left.write_bytes(before)
        right.write_bytes(after)
        result = subprocess.run(
            [
                "git",
                "diff",
                "--no-index",
                "--binary",
                "--no-ext-diff",
                "--no-textconv",
                str(left),
                str(right),
            ],
            capture_output=True,
            check=False,
            timeout=30,
        )
        if result.returncode != 1 or b"GIT binary patch" not in result.stdout:
            raise ValueError(f"Cannot generate binary brand patch: {path}")
        lines = result.stdout.decode("utf-8").splitlines(keepends=True)
        lines[0] = f"diff --git a/{path} b/{path}\n"
        return "".join(lines)


def render(root, snapshot, diff):
    overrides = {}

    def original(path):
        return (snapshot / path).read_text(
            encoding="latin-1" if path.endswith("module.ver") else "utf-8"
        )

    def update(path, replacements):
        text = original(path)
        for before, after in replacements:
            text = once(text, before, after)
        overrides[path] = text

    update(
        BASE + "configure.sh",
        [
            ("MOZ_APP_DISPLAYNAME=Nightly", "MOZ_APP_DISPLAYNAME='Lumen Browser'"),
            (
                "MOZ_MACBUNDLE_ID=nightlyunofficial",
                "MOZ_MACBUNDLE_ID=io.github.seanshaffer88.lumenbrowser",
            ),
        ],
    )
    overrides[BASE + "locales/en-US/brand.ftl"] = (
        HEADER
        + '## Lumen product names are not translated.\n\n-brand-shorter-name = Lumen Browser\n-brand-short-name = Lumen Browser\n-brand-shortcut-name = Lumen Browser\n-brand-full-name = Lumen Browser\n-brand-product-name = Lumen Browser\n-vendor-short-name = Lumen Project\ntrademarkInfo = { " " }\n'
    )
    overrides[BASE + "locales/en-US/brand.properties"] = (
        HEADER
        + "brandShorterName=Lumen Browser\nbrandShortName=Lumen Browser\nbrandFullName=Lumen Browser\n"
    )
    text = original(BASE + "branding.nsi")
    for key, value in {
        "BrandFullNameInternal": "Lumen",
        "BrandFullName": "Lumen Browser",
        "CompanyName": "Lumen Project",
        "URLInfoAbout": REPO,
        "HelpLink": REPO + "/issues",
        "URLStubDownloadX86": "",
        "URLStubDownloadAMD64": "",
        "URLStubDownloadAArch64": "",
        "URLManualDownload": REPO + "/releases",
        "URLSystemRequirements": REPO + "/blob/main/docs/COMPATIBILITY.md",
    }.items():
        text, count = re.subn(
            rf'^!define {key}\s+"[^"\n]*"$',
            f'!define {key} "{value}"',
            text,
            flags=re.M,
        )
        if count != 1:
            raise ValueError(f"Missing NSIS brand define: {key}")
    overrides[BASE + "branding.nsi"] = text
    overrides[BASE + "pref/firefox-branding.js"] = (
        HEADER.replace("# ", "// ")
        + f'pref("startup.homepage_override_url", "");\npref("startup.homepage_welcome_url", "about:preferences#lumen");\npref("startup.homepage_welcome_url.additional", "");\npref("app.update.url", "");\npref("app.update.url.manual", "{REPO}/releases");\npref("app.update.url.details", "{REPO}");\n'
    )
    svg = (root / "branding/lumen.svg").read_text(encoding="utf-8-sig")
    for name in ("about-logo.svg", "document_pdf.svg"):
        overrides[BASE + "content/" + name] = svg
    for name in ("about-wordmark.svg", "firefox-wordmark.svg"):
        overrides[BASE + "content/" + name] = (
            svg[: svg.index("<svg")]
            + '<svg xmlns="http://www.w3.org/2000/svg" width="370" height="64" viewBox="0 0 370 64"><text x="0" y="49" font-family="Segoe UI, sans-serif" font-size="42" font-weight="600" fill="#c52b36">Lumen Browser</text></svg>\n'
        )
    for name in (
        "firefox.VisualElementsManifest.xml",
        "private_browsing.VisualElementsManifest.xml",
    ):
        overrides[BASE + name] = original(BASE + name).replace("#14171a", "#121214")
    overrides[BASE + "lumen.VisualElementsManifest.xml"] = overrides[
        BASE + "firefox.VisualElementsManifest.xml"
    ]
    update(
        "browser/branding/branding-common.mozbuild",
        [
            (
                '"firefox.VisualElementsManifest.xml"',
                '"lumen.VisualElementsManifest.xml"',
            )
        ],
    )
    app = "browser/app/moz.build"
    overrides[app] = (
        original(app)
        + '\nFINAL_TARGET_FILES.distribution += ["distribution/policies.json"]\n'
    )
    overrides["browser/app/distribution/policies.json"] = (
        '{\n  "policies": {\n    "DisableAppUpdate": true,\n    "DontCheckDefaultBrowser": true\n  }\n}\n'
    )
    overrides["browser/installer/package-manifest.in"] = (
        once(
            original("browser/installer/package-manifest.in"),
            "firefox.VisualElementsManifest.xml",
            "lumen.VisualElementsManifest.xml",
        )
        + "\n; Lumen development update policy is shipped in every build.\n@RESPATH@/distribution/policies.json\n"
    )
    path = "browser/installer/windows/nsis/defines.nsi.in"
    text = original(path)
    for key in ("AppName", "DDEApplication", "AppRegName", "BrandProductName"):
        text, count = re.subn(
            rf'^!define {key}\s+"Firefox"$', f'!define {key} "Lumen"', text, flags=re.M
        )
        if count != 1:
            raise ValueError(f"Missing product identity: {key}")
    overrides[path] = text
    path = "browser/installer/windows/nsis/installer.nsi"
    text = original(path)
    text = once(
        text,
        "Page custom preOptions leaveOptions",
        "; Lumen uses one clear flow: location, shortcuts, review.",
    )
    text = once(
        text,
        """!ifdef HAVE_64BIT_BUILD
  InstallDir "$PROGRAMFILES64\\${BrandFullName}\\"
!else
  InstallDir "$PROGRAMFILES32\\${BrandFullName}\\"
!endif""",
        'InstallDir "$LOCALAPPDATA\\Lumen Browser\\"',
    )
    text = once(
        text,
        "  ShowWindow $0 ${SW_SHOW}\nFunctionEnd\n\nFunction preOptions",
        "  ShowWindow $0 ${SW_SHOW}\n  StrCpy $InstallType ${INSTALLTYPE_CUSTOM}\n  ${LeaveOptionsCommon}\nFunctionEnd\n\nFunction preOptions",
    )
    text = once(
        text,
        "Function leaveDirectory\n",
        "Function leaveDirectory\n  Call CheckLumenInstallTarget\n",
    )
    text = once(
        text,
        'Section "-InstallStartCleanup"\n',
        'Section "-InstallStartCleanup"\n  Call CheckLumenInstallTarget\n',
    )
    text += (
        "\nFunction CheckLumenInstallTarget\n"
        '  ${If} ${FileExists} "$INSTDIR\\firefox.exe"\n'
        '  ${OrIf} ${FileExists} "$INSTDIR\\chrome.exe"\n'
        '  ${OrIf} ${FileExists} "$INSTDIR\\msedge.exe"\n'
        "    SetErrorLevel 2\n"
        '    MessageBox MB_OK|MB_ICONSTOP "Choose a separate folder. Lumen Browser cannot replace another browser." /SD IDOK\n'
        "    Abort\n"
        "  ${EndIf}\n"
        "  SetErrorLevel 0\n"
        "FunctionEnd\n"
    )
    for field in (2, 4):
        text = once(
            text,
            f'WriteINIStr "$PLUGINSDIR\\shortcuts.ini" "Field {field}" State  "1"',
            f'WriteINIStr "$PLUGINSDIR\\shortcuts.ini" "Field {field}" State  "0"',
        )
    for variable in ("AddDesktopSC", "AddPrivateBrowsingSC"):
        text = once(text, f'    StrCpy ${variable} "1"', f'    StrCpy ${variable} "0"')
    text = once(
        text,
        "    ${GetPinningSupportedByWindowsVersionWithoutSystemPopup} $AddTaskbarSC",
        '    StrCpy $AddTaskbarSC "0"',
    )
    text = once(
        text,
        '  ${InstallOnInitCommon} "$(WARN_MIN_SUPPORTED_OSVER_CPU_MSG2)"',
        '  ${InstallOnInitCommon} "$(WARN_MIN_SUPPORTED_OSVER_CPU_MSG2)"\n'
        "  ${GetParameters} $0\n"
        "  ClearErrors\n"
        '  ${GetOptions} "$0" "/NoShortcuts" $1\n'
        "  ${Unless} ${Errors}\n"
        '    StrCpy $AddDesktopSC "0"\n'
        '    StrCpy $AddStartMenuSC "0"\n'
        '    StrCpy $AddTaskbarSC "0"\n'
        '    StrCpy $AddPrivateBrowsingSC "0"\n'
        "  ${EndUnless}\n"
        "  ClearErrors\n",
    )
    text = once(
        text,
        "Function .onInit\n",
        "Function .onInit\n"
        "  ${GetParameters} $0\n"
        "  ClearErrors\n"
        '  ${GetOptions} "$0" "/Help" $1\n'
        "  ${Unless} ${Errors}\n"
        '    MessageBox MB_OK "Lumen Browser Setup options:$\\r$\\n/S - silent installation$\\r$\\n/InstallDirectoryPath=$\\"C:\\Folder\\Lumen Browser$\\"$\\r$\\n/DesktopShortcut=true|false$\\r$\\n/StartMenuShortcut=true|false$\\r$\\n/TaskbarShortcut=true|false$\\r$\\n/PrivateBrowsingShortcut=true|false$\\r$\\n/NoShortcuts - create no shortcuts or taskbar pins$\\r$\\n/Help - show this help" /SD IDOK\n'
        "    SetErrorLevel 0\n"
        "    Quit\n"
        "  ${EndUnless}\n"
        "  ClearErrors\n",
    )
    text = once(
        text,
        '  WriteRegDWORD HKCU ${MOZ_LAUNCHER_SUBKEY} "$INSTDIR\\${FileMainEXE}|Telemetry" 1',
        '  WriteRegDWORD HKCU ${MOZ_LAUNCHER_SUBKEY} "$INSTDIR\\${FileMainEXE}|Telemetry" 0',
    )
    for field, variable, default in (
        (2, "AddDesktopSC", "0"),
        (3, "AddStartMenuSC", "1"),
        (4, "AddTaskbarSC", "0"),
    ):
        boundary = f'WriteINIStr "$PLUGINSDIR\\shortcuts.ini" "Field {field}" State  "{default}"'
        text = once(
            text,
            boundary,
            boundary
            + f'\n  ${{If}} ${variable} != ""\n    WriteINIStr "$PLUGINSDIR\\shortcuts.ini" "Field {field}" State "${variable}"\n  ${{EndIf}}',
        )
    text = start_menu_folder(text)
    text = text.replace('"Mozilla\\Firefox"', '"Lumen\\Lumen"')
    for name in ("SendPingIfApplicable", "WriteInstallationTelemetryData"):
        text = nsis_function(text, name, "  Return\n")
    text = nsis_function(
        text,
        "CustomAbort",
        '  MessageBox MB_YESNO|MB_ICONEXCLAMATION "$(MOZ_MUI_TEXT_ABORTWARNING)" IDYES +1 IDNO +2\n  Return\n  Abort\n',
    )
    match = re.search(r"^Function preSummary\n.*?^FunctionEnd\n", text, re.M | re.S)
    if not match:
        raise ValueError("Missing installer summary function")
    summary = match.group(0).replace('"Field 4"', '"Field 5"')
    summary = once(summary, '"Settings" NumFields "4"', '"Settings" NumFields "5"')
    summary = once(summary, '"Settings" NumFields "3"', '"Settings" NumFields "4"')
    choices = (
        '  StrCpy $0 ""\n'
        '  ${If} $AddDesktopSC == "1"\n'
        '    StrCpy $0 "$(LUMEN_SUMMARY_DESKTOP)"\n'
        "  ${EndIf}\n"
        '  ${If} $AddStartMenuSC == "1"\n'
        '    ${If} $0 != ""\n'
        '      StrCpy $0 "$0, "\n'
        "    ${EndIf}\n"
        '    StrCpy $0 "$0$(LUMEN_SUMMARY_STARTMENU)"\n'
        "  ${EndIf}\n"
        '  ${If} $AddTaskbarSC == "1"\n'
        '    ${If} $0 != ""\n'
        '      StrCpy $0 "$0, "\n'
        "    ${EndIf}\n"
        '    StrCpy $0 "$0$(LUMEN_SUMMARY_TASKBAR)"\n'
        "  ${EndIf}\n"
        '  ${If} $0 == ""\n'
        '    StrCpy $0 "$(LUMEN_SUMMARY_NONE)"\n'
        "  ${EndIf}\n"
        '  WriteINIStr "$PLUGINSDIR\\summary.ini" "Field 4" Type "label"\n'
        '  WriteINIStr "$PLUGINSDIR\\summary.ini" "Field 4" Text "$(LUMEN_SUMMARY_SHORTCUTS) $0"\n'
        '  WriteINIStr "$PLUGINSDIR\\summary.ini" "Field 4" Left "0"\n'
        '  WriteINIStr "$PLUGINSDIR\\summary.ini" "Field 4" Right "-1"\n'
        '  WriteINIStr "$PLUGINSDIR\\summary.ini" "Field 4" Top "55"\n'
        '  WriteINIStr "$PLUGINSDIR\\summary.ini" "Field 4" Bottom "100"\n\n'
    )
    summary = once(
        summary,
        '  !insertmacro MUI_HEADER_TEXT "$(SUMMARY_PAGE_TITLE)"',
        choices + '  !insertmacro MUI_HEADER_TEXT "$(SUMMARY_PAGE_TITLE)"',
    )
    text = text[: match.start()] + summary + text[match.end() :]
    overrides[path] = text
    path = "browser/installer/windows/nsis/uninstaller.nsi"
    text = original(path)
    for line in (
        "!define MUI_FINISHPAGE_SHOWREADME\n",
        "!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED\n",
        "!define MUI_FINISHPAGE_SHOWREADME_TEXT $(UN_SURVEY_CHECKBOX_LABEL)\n",
        "!define MUI_FINISHPAGE_SHOWREADME_FUNCTION un.Survey\n",
    ):
        text = once(text, line, "")
    text = nsis_function(text, "un.Survey", "  Return\n")
    text = nsis_function(text, "un.SendUninstallPing", "  Return\n")
    text = text.replace('"Mozilla\\Firefox"', '"Lumen\\Lumen"').replace(
        '"Software\\Mozilla\\Firefox"', '"Software\\Mozilla\\Lumen"'
    )
    text = text.replace(
        "  ${un.DeleteShortcuts}\n",
        '  ${un.DeleteShortcuts}\n  RMDir "$SMPROGRAMS\\Lumen Browser"\n',
    )
    overrides[path] = text
    path = "browser/installer/windows/nsis/shared.nsh"
    shared = start_menu_folder(original(path))
    shared = once(
        shared,
        '"DisplayName" "${BrandFullNameInternal}$1"',
        '"DisplayName" "${BrandFullName}$1"',
    )
    shared = once(
        shared,
        '${UpdateOneShortcutBranding} "STARTMENU" "$SMPROGRAMS"',
        '${UpdateOneShortcutBranding} "STARTMENU" "$SMPROGRAMS" "Lumen Browser\\${BrandShortName}.lnk"',
    )
    shared = once(
        shared,
        '${UpdateOneShortcutBranding} "DESKTOP" "$DESKTOP"',
        '${UpdateOneShortcutBranding} "DESKTOP" "$DESKTOP" "${BrandShortName}.lnk"',
    )
    macro = re.search(
        r"^!macro UpdateOneShortcutBranding LOG_SECTION SHORTCUT_DIR\n.*?^!macroend\n",
        shared,
        re.M | re.S,
    )
    if not macro:
        raise ValueError("Missing shortcut rename macro")
    body = (
        macro.group(0)
        .replace(
            "LOG_SECTION SHORTCUT_DIR\n", "LOG_SECTION SHORTCUT_DIR SHORTCUT_NAME\n"
        )
        .replace("${BrandShortName}.lnk", "${SHORTCUT_NAME}")
    )
    shared = shared[: macro.start()] + body + shared[macro.end() :]
    overrides[path] = shared
    path = "browser/installer/windows/nsis/install_dir_helpers.nsh"
    overrides[path] = once(
        original(path), '"$0\\Mozilla\\Firefox"', '"$0\\Lumen\\Lumen"'
    )
    path = "toolkit/mozapps/installer/windows/nsis/common.nsh"
    text = original(path)
    text = once(
        text,
        """      ${Else}
        ; If we weren't given a custom path parameter, then try to elevate now.
        ; We'll check the user's permission level later on to determine the
        ; default install path (which will be the real install path for /S).
        ; If an INI file is used, we try to elevate down that path when needed.
        ${ElevateUAC}
      ${EndIf}""",
        "      ${EndIf}",
    )
    overrides[path] = text
    path = "browser/locales/en-US/installer/mui.properties"
    text = original(path)
    for key, value in {
        "MUI_TEXT_DIRECTORY_TITLE": "Choose Installation Folder",
        "MUI_UNTEXT_FINISH_INFO_TEXT": "$BrandFullName has been removed.\\n\\nYour browsing data has been kept.\\n\\nClick Finish to close Setup.",
        "MUI_TEXT_WELCOME_INFO_TITLE": "Welcome to $BrandFullName Setup",
        "MUI_TEXT_WELCOME_INFO_TEXT": "Setup will install $BrandFullName for your Windows account. No internet connection is required.\\n\\nChoose an installation folder and the shortcuts you want to create. You can review your choices before installing.\\n\\n$_CLICK",
        "MUI_TEXT_FINISH_INFO_TEXT": "$BrandFullName has been installed. Your browser data is stored separately from the application.\\n\\nOpen Settings > Lumen Browser controls to customize your browser.\\n\\n$_CLICK",
    }.items():
        text, count = re.subn(
            rf"^{key}=.*$", lambda _: key + "=" + value, text, flags=re.M
        )
        if count != 1:
            raise ValueError(f"Missing installer message: {key}")
    overrides[path] = text
    path = "browser/locales/en-US/installer/custom.properties"
    text = original(path)
    values = {
        "REG_APP_DESC": "$BrandShortName is a customizable, privacy-focused web browser based on Firefox.",
        "BRIEF_APP_DESC": "Browse the web with $BrandShortName",
        "STATUS_CLEANUP": "Preparing installation…",
        "ICONS_DESKTOP": "Create &Desktop Shortcut",
        "ICONS_STARTMENU": "Create &Start Menu Shortcut",
        "ICONS_TASKBAR": "Pin to &Taskbar",
        "CREATE_ICONS_DESC": "Choose shortcuts for $BrandShortName:",
        "SHORTCUTS_PAGE_TITLE": "Choose Shortcuts",
        "SHORTCUTS_PAGE_SUBTITLE": "Choose which shortcuts to create.",
        "SUMMARY_PAGE_TITLE": "Review Your Installation",
        "SUMMARY_PAGE_SUBTITLE": "Review your choices before installing $BrandShortName.",
        "SUMMARY_INSTALL_CLICK": "Click Install to install $BrandShortName.",
        "UN_CONFIRM_UNINSTALLED_FROM": "$BrandShortName will be removed from the following folder:",
        "OPTION_CUSTOM_DESC": "Choose the location and shortcuts for your Windows account.",
    }
    for key, value in values.items():
        text, count = re.subn(
            rf"^{key}=.*$", lambda _: key + "=" + value, text, flags=re.M
        )
        if count != 1:
            raise ValueError(f"Missing installer message: {key}")
    text += (
        "\nLUMEN_SUMMARY_SHORTCUTS=Shortcuts:\nLUMEN_SUMMARY_DESKTOP=Desktop\n"
        "LUMEN_SUMMARY_STARTMENU=Start menu\nLUMEN_SUMMARY_TASKBAR=Taskbar\nLUMEN_SUMMARY_NONE=No shortcuts\n"
    )
    for old_key, new_key in [
        ("WARN_MIN_SUPPORTED_OSVER_MSG", "WARN_MIN_SUPPORTED_OSVER_MSG2"),
        ("WARN_MIN_SUPPORTED_OSVER_CPU_MSG", "WARN_MIN_SUPPORTED_OSVER_CPU_MSG2"),
    ]:
        message = re.search(rf"^{old_key}=(.*)$", text, re.M)
        if not message:
            raise ValueError("Missing minimum-OS installer message")
        text += new_key + "=" + message.group(1) + "\n"
    overrides[path] = text
    overrides["browser/installer/windows/app.tag"] = once(
        original("browser/installer/windows/app.tag"),
        'Title="Mozilla Firefox"',
        'Title="Lumen Browser Setup"',
    )
    sfx_source = "other-licenses/7zstub/src/CPP/7zip/Bundles/SFXSetup/SfxSetup.cpp"
    before_sfx = original(sfx_source)
    after_sfx = once(
        before_sfx,
        "    WaitForSingleObject(hProcess, INFINITE);\n",
        "    const DWORD waitResult = WaitForSingleObject(hProcess, INFINITE);\n"
        "    if (waitResult != WAIT_OBJECT_0 || !GetExitCodeProcess(hProcess, &exitCode))\n"
        "    {\n"
        "      ::CloseHandle(hProcess);\n"
        "      return ERROR_INSTALL_FAILURE;\n"
        "    }\n",
    )
    after_sfx = once(
        after_sfx,
        "  if (hProcess != 0)\n",
        "  DWORD exitCode = 0;\n  if (hProcess != 0)\n",
    )
    after_sfx = once(
        after_sfx, "  return 0;\n}\n", "  return static_cast<int>(exitCode);\n}\n"
    )
    overrides[sfx_source] = after_sfx
    readme = "other-licenses/7zstub/README.mozilla"
    overrides[readme] = (
        original(readme)
        + "\nLumen Browser downstream change\n-------------------------------\nThe generated Lumen downstream overlay records child exit-code propagation.\nMozilla's existing customization record above is retained unchanged. Lumen's\nWindows packager builds this patched source using its local SDK, then brands\nthe temporary unsigned SFX. No precompiled replacement is committed.\n"
    )
    overrides["python/mozbuild/mozbuild/action/lumen_sfx_build.py"] = (
        root / "tools/sfx_builder.py"
    ).read_text(encoding="utf-8")
    overrides["python/mozbuild/mozbuild/action/lumen_sfx.py"] = (
        root / "tools/sfx_resources.py"
    ).read_text(encoding="utf-8-sig")
    archive = "python/mozbuild/mozbuild/action/exe_7z_archive.py"
    overrides[archive] = once(
        original(archive),
        "        if use_upx:\n",
        """        from mozbuild.action.lumen_sfx import brand_sfx
        from mozbuild.action.lumen_sfx_build import build_sfx

        compiled_sfx = build_sfx(buildconfig.topsrcdir, tmpdir)
        branded_sfx = mozpath.join(tmpdir, "LumenSetup.sfx")
        brand_sfx(
            compiled_sfx,
            branded_sfx,
            mozpath.join(
                buildconfig.topsrcdir,
                buildconfig.substs["MOZ_BRANDING_DIRECTORY"],
                "firefox.ico",
            ),
            buildconfig.substs.get("MOZ_APP_VERSION", "development"),
        )
        sfx_package = branded_sfx

        if use_upx:
""",
    )
    manager = "browser/components/shell/CustomIconManager.sys.mjs"
    text = original(manager)
    text = once(
        text,
        '      Services.dirsvc.get("Progs", Ci.nsIFile).path,\n',
        '      Services.dirsvc.get("Progs", Ci.nsIFile).path,\n      "Lumen Browser",\n',
    )
    text = once(
        text,
        '    let name = AppConstants.MOZ_APP_DISPLAYNAME_DO_NOT_USE + ".lnk";',
        '    let name =\n      "Lumen Browser\\\\" + AppConstants.MOZ_APP_DISPLAYNAME_DO_NOT_USE + ".lnk";',
    )
    overrides[manager] = text
    shell = "browser/components/shell/nsWindowsShellService.cpp"
    text = original(shell)
    text = once(
        text,
        "    collectTagged(nsDependentString(folderPath.get()), folder.location);\n",
        "    collectTagged(nsDependentString(folderPath.get()), folder.location);\n"
        "    if (folder.folderId == FOLDERID_Programs ||\n"
        "        folder.folderId == FOLDERID_CommonPrograms) {\n"
        "      nsAutoString lumenFolder(folderPath.get());\n"
        '      lumenFolder.AppendLiteral("\\\\Lumen Browser");\n'
        "      collectTagged(lumenFolder, folder.location);\n"
        "    }\n",
    )
    overrides[shell] = text
    # The upstream generator collected module.ver dependencies but discarded them.
    # Record configuration too, so incremental public-name changes rebuild resources.
    resource_generator = "config/create_rc.py"
    overrides[resource_generator] = once(
        original(resource_generator),
        "    if dep_file is not None and extra_deps:\n",
        "    extra_deps.update(deps)\n"
        '    extra_deps.add(os.path.join(buildconfig.topobjdir, "config", "autoconf.mk"))\n'
        "    if dep_file is not None and extra_deps:\n",
    )
    # Append ASCII overrides: preserve the legacy copyright bytes verbatim.
    # create_rc.parse_module_ver deliberately uses the last assignment.
    for path in ("browser/app/module.ver", "browser/app/pbproxy/module.ver"):
        overrides[path] = original(path) + (
            "\n# Lumen public Windows metadata overrides.\n"
            "WIN32_MODULE_COMPANYNAME=Lumen Project\n"
            "WIN32_MODULE_DESCRIPTION=Lumen Browser\n"
            "WIN32_MODULE_PRODUCTNAME=Lumen Browser\n"
            "WIN32_MODULE_NAME=Lumen Browser\n"
        )
    patch = ""
    for path, after in sorted(overrides.items()):
        before = original(path) if (snapshot / path).exists() else ""
        if path == sfx_source:
            before = (snapshot / path).read_bytes().decode("utf-8")
            after = after.replace("\n", "\r\n")
        patch += diff(path, before, after)
    for path, asset in sorted(BINARY.items()):
        patch += binary_diff(
            path,
            (snapshot / path).read_bytes(),
            (root / "branding/assets" / asset).read_bytes(),
        )
    return patch
