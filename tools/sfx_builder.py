# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Build the patched upstream Win32 SFX using a local, isolated Windows SDK."""

import concurrent.futures
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


def _latest(directory):
    versions = [
        p
        for p in directory.iterdir()
        if p.is_dir() and all(x.isdigit() for x in p.name.split("."))
    ]
    if not versions:
        raise ValueError(f"No versioned toolchain directory: {directory}")
    return max(versions, key=lambda p: tuple(map(int, p.name.split("."))))


def build_sfx(topsrcdir, temporary_root):
    if os.name != "nt":
        raise OSError("Building the Lumen installer SFX requires native Windows")
    state = Path(os.environ.get("MOZBUILD_STATE_PATH", Path.home() / ".mozbuild"))
    vs = Path(
        os.environ.get("LUMEN_VS_ROOT", os.environ.get("VSINSTALLDIR", state / "vs"))
    )
    vc = _latest(vs / "VC/Tools/MSVC")
    sdk = Path(
        os.environ.get(
            "LUMEN_WINDOWS_SDK_ROOT",
            os.environ.get("WindowsSdkDir", vs / "Windows Kits/10"),
        )
    )
    version = _latest(sdk / "Include").name
    tools = vc / "bin/Hostx64/x86"
    compiler, linker = tools / "cl.exe", tools / "link.exe"
    resource_compiler = sdk / "bin" / version / "x64/rc.exe"
    for tool in (compiler, linker, resource_compiler):
        if not tool.is_file():
            raise ValueError(f"Missing SFX build tool: {tool}")

    work = Path(temporary_root) / "lumen-sfx-build"
    work.mkdir()
    original = Path(topsrcdir) / "other-licenses/7zstub"
    shutil.copytree(original / "src", work / "src")
    project = work / "firefox"
    project.mkdir()
    for name in (
        "SFXSetup.vcxproj",
        "resource.rc",
        "setup.ico",
        "7zSD.win32.manifest",
        "7zSD.arm64.manifest",
    ):
        shutil.copyfile(original / "firefox" / name, project / name)

    environment = {
        key: os.environ[key]
        for key in ("SystemRoot", "WINDIR", "TEMP", "TMP", "USERPROFILE")
        if key in os.environ
    }
    system = os.environ["SystemRoot"]
    environment["PATH"] = ";".join(
        map(str, (tools, resource_compiler.parent, Path(system) / "System32", system))
    )
    environment["INCLUDE"] = ";".join(
        map(
            str,
            [
                vc / "include",
                *[
                    sdk / "Include" / version / name
                    for name in ("ucrt", "shared", "um", "winrt")
                ],
            ],
        )
    )
    environment["LIB"] = ";".join(
        map(
            str,
            (
                vc / "lib/x86",
                sdk / "Lib" / version / "ucrt/x86",
                sdk / "Lib" / version / "um/x86",
            ),
        )
    )
    namespace = {"m": "http://schemas.microsoft.com/developer/msbuild/2003"}
    manifest = ET.parse(project / "SFXSetup.vcxproj").getroot()
    files = [
        (project / node.attrib["Include"].replace("\\", "/")).resolve()
        for node in manifest.findall(".//m:ClCompile[@Include]", namespace)
    ]
    if not files or any(
        not file.is_relative_to((work / "src").resolve()) for file in files
    ):
        raise ValueError("Invalid SFX compilation manifest")
    objects = work / "objects"
    objects.mkdir()
    defines = (
        "NDEBUG",
        "WIN32",
        "_WINDOWS",
        "EXTRACT_ONLY",
        "NO_REGISTRY",
        "_SFX",
        "_NO_CRYPTO",
        "UNICODE",
        "_UNICODE",
        "WINVER=0x0A00",
        "_WIN32_WINNT=0x0A00",
    )

    def compile_unit(item):
        index, source = item
        output = objects / f"{index}.obj"
        command = [
            str(compiler),
            "/nologo",
            "/c",
            "/O1",
            "/Os",
            "/MT",
            "/Gz",
            "/GS",
            "/W4",
            "/WX",
            "/I" + str(work / "src/CPP/7zip/Bundles/SFXSetup"),
            *["/D" + value for value in defines],
            "/Fo" + str(output),
            str(source),
        ]
        if source.name in ("Lzma2Dec.c", "Lzma2DecMt.c"):
            command.insert(2, "/wd5286")
        if source.suffix.lower() == ".cpp":
            command[2:2] = ["/EHsc", "/GR-"]
        result = subprocess.run(
            command,
            cwd=project,
            env=environment,
            capture_output=True,
            check=False,
            timeout=120,
        )
        if result.returncode:
            raise RuntimeError(
                result.stdout.decode(errors="replace")
                + result.stderr.decode(errors="replace")
            )
        return output

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        compiled = list(executor.map(compile_unit, enumerate(files)))
    resource = objects / "resource.res"
    subprocess.run(
        [
            str(resource_compiler),
            "/nologo",
            "/dNDEBUG",
            "/fo" + str(resource),
            "resource.rc",
        ],
        cwd=project,
        env=environment,
        check=True,
        timeout=120,
    )
    output = work / "7zSD.Lumen.Win32.sfx"
    libraries = (
        "kernel32",
        "user32",
        "gdi32",
        "winspool",
        "comdlg32",
        "advapi32",
        "shell32",
        "ole32",
        "oleaut32",
        "uuid",
        "odbc32",
        "odbccp32",
        "delayimp",
    )
    subprocess.run(
        [
            str(linker),
            "/NOLOGO",
            "/SUBSYSTEM:WINDOWS,6.02",
            "/MACHINE:X86",
            "/DYNAMICBASE",
            "/NXCOMPAT",
            "/SAFESEH",
            "/OPT:REF",
            "/OPT:ICF",
            "/OUT:" + str(output),
            *map(str, compiled),
            str(resource),
            *[name + ".lib" for name in libraries],
            "/DELAYLOAD:user32.dll",
            "/DELAYLOAD:shell32.dll",
            "/DELAYLOAD:oleaut32.dll",
        ],
        cwd=project,
        env=environment,
        check=True,
        timeout=120,
    )
    if not output.is_file():
        raise RuntimeError("SFX linker did not produce the expected output")
    return output
