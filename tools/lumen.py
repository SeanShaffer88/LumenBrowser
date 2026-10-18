"""MPL-2.0. Offline, deterministic Firefox patch preparation. Python 3.11+."""
from __future__ import annotations

import argparse
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PREF_FILE = "browser/app/profile/firefox.js"
TEST_DIR = "browser/base/content/test/browser-protectionsUI"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify_inputs(root=ROOT):
    lock = read_json(root / "upstream.lock.json")
    if not re.fullmatch(r"[0-9a-f]{40}", lock["revision"]):
        raise ValueError("Invalid upstream commit")
    for entry in lock["files"]:
        rel = Path(entry["path"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("Unsafe upstream path")
        data = (root / "audit/upstream" / rel).read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"Audit snapshot hash mismatch: {rel}")
    settings = read_json(root / "config/preferences.json")
    texts = [(root / "audit/upstream" / e["path"]).read_text(encoding="utf-8")
             for e in lock["files"] if e["path"].endswith((".js", ".yaml"))]
    known = set()
    types = {}
    for text in texts:
        known.update(re.findall(r'(?:pref|sticky_pref)\("([^"\n]+)"', text))
        known.update(re.findall(r"^- name: (\S+)$", text, re.M))
        for name, literal in re.findall(r'(?:pref|sticky_pref)\("([^"\n]+)",\s*(true|false|"(?:[^"\\]|\\.)*"|-?\d+)(?=\s*[,\)])', text):
            types.setdefault(name, set()).add(type(json.loads(literal)))
        for name, kind in re.findall(r"^- name: (\S+)\n\s+type: (\S+)", text, re.M):
            if "bool" in kind.lower():
                types.setdefault(name, set()).add(bool)
            elif "int" in kind.lower():
                types.setdefault(name, set()).add(int)
    seen = set()
    for item in settings:
        name = item["name"]
        if name in seen or name not in known:
            raise ValueError(f"Duplicate or unverified preference: {name}")
        if type(item["value"]) not in (bool, int, str):
            raise ValueError(f"Unsupported preference type: {name}")
        if types.get(name) != {type(item["value"])}:
            raise ValueError(f"Preference type differs from upstream or is ambiguous: {name}")
        if isinstance(item["value"], int) and not isinstance(item["value"], bool):
            if not -(2**31) <= item["value"] < 2**31:
                raise ValueError(f"Preference out of range: {name}")
        if not item["effect"] or item["risk"] not in ("privacy", "compatibility"):
            raise ValueError(f"Missing explanation or risk: {name}")
        seen.add(name)
    validate_catalog(root, types)
    return lock, settings


def validate_catalog(root, types):
    catalog = read_json(root / "config/customization.json")
    if not isinstance(catalog, list) or not 1 <= len(catalog) <= 200:
        raise ValueError("Invalid customization catalog size")
    by_name = {}
    kinds = {"bool": bool, "int": int, "string": str}
    for item in catalog:
        name = item["pref"]
        kind = kinds.get(item["type"])
        if name in by_name or kind is None or types.get(name) != {kind}:
            raise ValueError(f"Duplicate or incorrectly typed customization: {name}")
        for field in ("title", "description", "category"):
            if not isinstance(item[field], str) or not item[field] or re.search(r"[\r\n{}]", item[field]):
                raise ValueError(f"Invalid customization {field}: {name}")
        if not re.fullmatch(r"[a-z]+", item["category"]):
            raise ValueError(f"Invalid customization category: {name}")
        if kind is not bool and not item.get("options"):
            raise ValueError(f"Non-boolean setting requires bounded choices: {name}")
        values = []
        for option in item.get("options", []):
            value = option["value"]
            if type(value) is not kind or value in values or not option.get("label") or re.search(r"[\r\n{}]", option["label"]):
                raise ValueError(f"Invalid customization choices: {name}")
            if kind is int and not -(2**31) <= value < 2**31:
                raise ValueError(f"Customization integer out of range: {name}")
            values.append(value)
        if "warning" in item:
            if not item["warning"] or re.search(r"[\r\n{}]", item["warning"]) or not item.get("warnValues"):
                raise ValueError(f"Missing customization warning criteria: {name}")
            if any(type(value) is not kind or (values and value not in values) for value in item["warnValues"]):
                raise ValueError(f"Invalid customization warning criteria: {name}")
        by_name[name] = item
    for name, item in by_name.items():
        visited = {name}
        while "dependsOn" in item:
            dependency = item["dependsOn"]
            parent = dependency["pref"]
            if parent not in by_name or parent in visited:
                raise ValueError(f"Missing or cyclic customization dependency: {name}")
            item = by_name[parent]
            if type(dependency["value"]) is not kinds[item["type"]]:
                raise ValueError(f"Incorrect dependency value type: {name}")
            visited.add(parent)
    return catalog


def replace_once(source, before, after):
    if source.count(before) != 1:
        raise ValueError(f"Unexpected upstream integration boundary: {before[:80]}")
    return source.replace(before, after, 1)


def diff(path, before, after):
    return "".join(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile=f"a/{path}" if before else "/dev/null", tofile=f"b/{path}", n=3))


def replace_function(source, name, body):
    nodes = [node for node in ast.parse(source).body
             if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(nodes) != 1:
        raise ValueError(f"Unexpected upstream function boundary: {name}")
    node = nodes[0]
    lines = source.splitlines(keepends=True)
    replacement = lines[node.lineno - 1] + body
    return "".join(lines[:node.lineno - 1]) + replacement + "".join(lines[node.end_lineno:])


def render_patch(root=ROOT):
    lock, settings = verify_inputs(root)
    snapshot = root / "audit/upstream"
    original = (snapshot / PREF_FILE).read_text(encoding="utf-8")
    defaults = "\n// Lumen development defaults; see config/preferences.json.\n"
    for item in settings:
        defaults += f'pref({json.dumps(item["name"])}, {json.dumps(item["value"])});\n'
    patch = diff(PREF_FILE, original, original + defaults)
    # Remove the app-level implication instead of supplying contradictory flags.
    configure = "browser/moz.configure"
    original = (snapshot / configure).read_text(encoding="utf-8")
    updated = original
    for flag in ("MOZ_SERVICES_HEALTHREPORT", "MOZ_NORMANDY"):
        needle = f'imply_option("{flag}", True)\n'
        if updated.count(needle) != 1:
            raise ValueError(f"Unexpected upstream configure boundary: {flag}")
        updated = updated.replace(needle, f'# Lumen: {flag} intentionally not implied.\n')
    patch += diff(configure, original, updated)
    telemetry = "python/mach/mach/telemetry.py"
    original = (snapshot / telemetry).read_text(encoding="utf-8")
    updated = replace_function(original, "create_telemetry_from_environment",
                               "    from mach.telemetry_interface import NoopTelemetry\n\n"
                               "    return NoopTelemetry(False)\n")
    updated = replace_function(updated, "is_telemetry_enabled", "    return False\n")
    updated = replace_function(updated, "initialize_telemetry_setting", "    return None\n")
    patch += diff(telemetry, original, updated)
    nimbus = "toolkit/components/nimbus/ExperimentAPI.sys.mjs"
    original = (snapshot / nimbus).read_text(encoding="utf-8")
    updated = replace_once(original,
                           '  get labsEnabled() {\n    return Services.policies.isAllowed("FirefoxLabs");\n  }',
                           '  get labsEnabled() {\n    return false;\n  }')
    updated = replace_once(updated,
                           '  get rolloutsEnabled() {\n    return (\n      this.#prefValues.rolloutsEnabled &&\n'
                           '      Services.policies.isAllowed("NimbusRollouts")\n    );\n  }',
                           '  get rolloutsEnabled() {\n    return false;\n  }')
    updated = replace_once(updated, '  get studiesEnabled() {\n    return this.#studiesEnabled;\n  }',
                           '  get studiesEnabled() {\n    return false;\n  }')
    patch += diff(nimbus, original, updated)
    test_name = "browser_lumen_defaults.js"
    manifest = f"{TEST_DIR}/browser.toml"
    original = (snapshot / manifest).read_text(encoding="utf-8")
    if test_name in original:
        raise ValueError("Lumen test already registered upstream")
    patch += diff(manifest, original, original + f'\n["{test_name}"]\n')
    test = '// SPDX-License-Identifier: MPL-2.0\n"use strict";\n\n'
    test += "add_task(function lumen_default_preferences() {\n"
    test += "  const defaults = Services.prefs.getDefaultBranch(\"\");\n"
    for item in settings:
        kind = {bool: "Bool", int: "Int", str: "String"}[type(item["value"])]
        name, value = json.dumps(item["name"]), json.dumps(item["value"])
        test += f'  Assert.equal(defaults.get{kind}Pref({name}), {value}, {name});\n'
    test += '  const { ExperimentAPI } = ChromeUtils.importESModule("resource://nimbus/ExperimentAPI.sys.mjs");\n'
    test += '  Assert.ok(!ExperimentAPI.enabled, "Nimbus remote experiments are disabled");\n'
    test += '  Assert.ok(!ExperimentAPI.labsEnabled, "Labs cannot keep the remote loader enabled");\n'
    test += "});\n"
    patch += diff(f"{TEST_DIR}/{test_name}", "", test)
    patch += settings_patch(root, snapshot)
    return lock, patch


def settings_patch(root, snapshot):
    catalog = read_json(root / "config/customization.json")
    directory = "browser/components/preferences"
    path = f"{directory}/preferences.js"
    original = (snapshot / path).read_text(encoding="utf-8")
    updated = replace_once(original, '/* import-globals-from main.js */',
                           '/* import-globals-from main.js */\n/* import-globals-from lumen.js */')
    updated = replace_once(updated, '  register_module("panePrivacy", gPrivacyPane);',
                           '  register_module("panePrivacy", gPrivacyPane);\n  register_module("paneLumen", gLumenPane);')
    patch = diff(path, original, updated)
    path = f"{directory}/preferences.xhtml"
    original = (snapshot / path).read_text(encoding="utf-8")
    updated = replace_once(original, '  <link rel="localization" href="branding/brand.ftl"/>',
                           '  <link rel="localization" href="browser/preferences/lumen.ftl"/>\n'
                           '  <link rel="stylesheet" href="chrome://browser/content/preferences/lumen.css"/>\n'
                           '  <script src="chrome://browser/content/preferences/lumen.js"/>\n'
                           '  <link rel="localization" href="branding/brand.ftl"/>')
    marker = '      <html:moz-page-nav-button id="category-general"'
    updated = replace_once(updated, marker,
                           '      <html:moz-page-nav-button id="category-lumen" view="paneLumen"\n'
                           '        iconsrc="chrome://global/skin/icons/settings.svg"\n'
                           '        data-l10n-id="lumen-title"/>\n' + marker)
    updated = replace_once(updated, '#include privacy.inc.xhtml', '#include privacy.inc.xhtml\n#include lumen.inc.xhtml')
    patch += diff(path, original, updated)
    path = f"{directory}/jar.mn"
    original = (snapshot / path).read_text(encoding="utf-8")
    additions = ["lumen.js", "lumen.css", "lumen/settings-model.mjs", "lumen/catalog.mjs"]
    updated = original + "".join(f"   content/browser/preferences/{name} ({name})\n" for name in additions)
    patch += diff(path, original, updated)
    assets = {"settings.js": "lumen.js", "settings.css": "lumen.css",
              "settings.inc.xhtml": "lumen.inc.xhtml", "settings-model.mjs": "lumen/settings-model.mjs"}
    for local, target in assets.items():
        patch += diff(f"{directory}/{target}", "", (root / "browser" / local).read_text(encoding="utf-8"))
    runtime_catalog = "// SPDX-License-Identifier: MPL-2.0\nexport const LUMEN_CATALOG = " + json.dumps(catalog, indent=2) + ";\n"
    patch += diff(f"{directory}/lumen/catalog.mjs", "", runtime_catalog)
    locale = (root / "browser/lumen.ftl").read_text(encoding="utf-8")
    for index, item in enumerate(catalog):
        prefix = f"lumen-setting-{index}"
        for field in ("title", "description", "warning"):
            if field in item:
                locale += f"{prefix}-{field} = {item[field]}\n"
        for option_index, option in enumerate(item.get("options", [])):
            locale += f'{prefix}-option-{option_index} = {option["label"]}\n'
    patch += diff("browser/locales/en-US/browser/preferences/lumen.ftl", "", locale)
    path = f"{directory}/tests/browser.toml"
    original = (snapshot / path).read_text(encoding="utf-8")
    updated = original + '\n["browser_lumen_controls.js"]\n'
    patch += diff(path, original, updated)
    patch += diff(f"{directory}/tests/browser_lumen_controls.js", "",
                  (root / "browser/browser_lumen_controls.js").read_text(encoding="utf-8"))
    return patch


def atomic_write(path, data):
    """Replace one generated artifact; preserve its prior content on write failure."""
    path = Path(path)
    if path.is_symlink() or path.is_dir():
        raise ValueError("Output must be a regular file, not a link or directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".lumen-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def check_source(source, lock, patch):
    """Read-only preflight; never checks out, resets, or edits a caller's tree."""
    source = Path(source).resolve(strict=True)
    def git(*args, input=None):
        result = subprocess.run(["git", "-C", str(source), *args], input=input,
                                capture_output=True, check=False, timeout=120)
        if result.returncode:
            raise ValueError(result.stderr.decode("utf-8", errors="replace").strip())
        return result.stdout.decode("utf-8").strip()
    top = Path(git("rev-parse", "--show-toplevel")).resolve()
    if top != source:
        raise ValueError("Source must be the repository root")
    if git("rev-parse", "HEAD") != lock["revision"]:
        raise ValueError("Source revision does not match upstream.lock.json")
    if git("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("Source tree is dirty; preserve your changes before preparing")
    git("apply", "--check", "--whitespace=error", "-", input=patch.encode("utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="Verify pinned snapshots and preference registry")
    prepare = commands.add_parser("patch", help="Emit patch; optionally preflight a full checkout")
    prepare.add_argument("--source", type=Path)
    prepare.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        lock, patch = render_patch()
        if args.command == "patch":
            if args.source:
                check_source(args.source, lock, patch)
            output = args.output.absolute()
            # Generated artifacts cannot overwrite source, configuration, or audit evidence.
            protected = [ROOT / name for name in ("audit", "config", "tools", "tests")]
            if args.source:
                protected.append(args.source.resolve())
            resolved = output.resolve()
            if any(resolved.is_relative_to(p.resolve()) for p in protected):
                raise ValueError("Output overlaps protected inputs or source checkout")
            if resolved.is_relative_to(ROOT) and not resolved.is_relative_to(ROOT / "out"):
                raise ValueError("Repository output must be under out/")
            atomic_write(output, patch.encode("utf-8"))
        print(json.dumps({"status": "ok", "revision": lock["revision"],
                          "browser_built": False, "network_verified": False}))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"lumen: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
