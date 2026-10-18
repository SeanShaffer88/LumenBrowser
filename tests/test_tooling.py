"""SPDX-License-Identifier: MPL-2.0"""
import importlib.util
import ast
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import types
import unittest
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

SPEC = importlib.util.spec_from_file_location("lumen", Path(__file__).resolve().parents[1] / "tools/lumen.py")
lumen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lumen)


class ToolingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def copy_inputs(self):
        for name in ("audit", "config"):
            shutil.copytree(lumen.ROOT / name, self.root / name)
        shutil.copyfile(lumen.ROOT / "upstream.lock.json", self.root / "upstream.lock.json")

    def test_snapshots_and_preferences_validate(self):
        lock, settings = lumen.verify_inputs()
        self.assertEqual(len(lock["revision"]), 40)
        self.assertGreater(len(settings), 20)

    def test_tampered_upstream_fails(self):
        self.copy_inputs()
        (self.root / "audit/upstream" / lumen.PREF_FILE).write_text("tampered")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            lumen.render_patch(self.root)

    def test_unknown_and_duplicate_preferences_fail(self):
        self.copy_inputs()
        config = self.root / "config/preferences.json"
        original = json.loads(config.read_text())
        for name in (original[1]["name"], "lumen.misspelled.preference"):
            items = json.loads(json.dumps(original))
            items[0]["name"] = name
            config.write_text(json.dumps(items))
            with self.assertRaisesRegex(ValueError, "Duplicate or unverified"):
                lumen.render_patch(self.root)

    def test_wrong_type_and_overflow_fail(self):
        self.copy_inputs()
        config = self.root / "config/preferences.json"
        original = json.loads(config.read_text())
        for value in (None, [], {}, 2**31, "false", 0):
            items = json.loads(json.dumps(original))
            items[0]["value"] = value
            config.write_text(json.dumps(items))
            with self.assertRaises(ValueError):
                lumen.render_patch(self.root)

    def test_customization_rejects_cycles_and_unbounded_choices(self):
        self.copy_inputs()
        path = self.root / "config/customization.json"
        original = json.loads(path.read_text())
        items = json.loads(json.dumps(original))
        items[0]["dependsOn"] = {"pref": items[0]["pref"], "value": True}
        path.write_text(json.dumps(items))
        with self.assertRaisesRegex(ValueError, "cyclic"):
            lumen.verify_inputs(self.root)
        items = json.loads(json.dumps(original))
        numeric = next(item for item in items if item["type"] == "int")
        numeric.pop("options")
        path.write_text(json.dumps(items))
        with self.assertRaisesRegex(ValueError, "bounded choices"):
            lumen.verify_inputs(self.root)

    def test_patch_is_deterministic_and_applies_then_reverses(self):
        _, delta = lumen.render_patch()
        self.assertEqual(delta, lumen.render_patch()[1])
        source = self.root / "source"
        shutil.copytree(lumen.ROOT / "audit/upstream", source)
        def git(*args):
            return subprocess.run(["git", "-C", str(source), *args],
                                  capture_output=True, check=True)
        git("init", "--quiet")
        git("config", "core.autocrlf", "false")
        before = {p.relative_to(source): p.read_bytes() for p in source.rglob("*")
                  if p.is_file() and ".git" not in p.parts}
        artifact = self.root / "lumen.patch"
        artifact.write_bytes(delta.encode())
        git("apply", "--check", "--whitespace=error", str(artifact))
        git("apply", str(artifact))
        generated = source / lumen.TEST_DIR / "browser_lumen_defaults.js"
        self.assertTrue(generated.is_file())
        self.assertIn("getDefaultBranch", generated.read_text())
        policies = json.loads((source / "browser/app/distribution/policies.json").read_text())
        self.assertTrue(policies["policies"]["DisableAppUpdate"])

        telemetry = (source / "python/mach/mach/telemetry.py").read_text()
        names = {"create_telemetry_from_environment", "is_telemetry_enabled", "initialize_telemetry_setting"}
        functions = [node for node in ast.parse(telemetry).body
                     if isinstance(node, ast.FunctionDef) and node.name in names]
        module = ast.Module(body=functions, type_ignores=[])
        namespace = {}
        exec(compile(module, "patched-telemetry", "exec"), namespace)
        fake_interface = types.ModuleType("mach.telemetry_interface")
        fake_interface.NoopTelemetry = lambda enabled: ("noop", enabled)
        with patch.dict("sys.modules", {"mach.telemetry_interface": fake_interface}):
            self.assertEqual(namespace["create_telemetry_from_environment"](object()), ("noop", False))
            self.assertFalse(namespace["is_telemetry_enabled"](object()))
            self.assertIsNone(namespace["initialize_telemetry_setting"](object(), None))
        git("apply", "--reverse", "--check", str(artifact))
        git("apply", "--reverse", str(artifact))
        self.assertFalse(generated.exists())
        for relative, content in before.items():
            self.assertEqual((source / relative).read_bytes(), content)

    def test_patch_preserves_missing_final_newline(self):
        source = self.root / "newline-case"
        source.mkdir()
        subprocess.run(["git", "-C", str(source), "init", "--quiet"], check=True)
        subprocess.run(["git", "-C", str(source), "config", "core.autocrlf", "false"], check=True)
        target = source / "file.svg"
        target.write_bytes(b"<svg/>")
        delta = lumen.diff("file.svg", "<svg/>", "<svg>updated</svg>\n").encode()
        subprocess.run(["git", "-C", str(source), "apply", "-"], input=delta, check=True)
        self.assertEqual(target.read_bytes(), b"<svg>updated</svg>\n")
        subprocess.run(["git", "-C", str(source), "apply", "--reverse", "-"], input=delta, check=True)
        self.assertEqual(target.read_bytes(), b"<svg/>")

    def test_interrupted_write_preserves_old_file(self):
        output = self.root / "result.patch"
        output.write_bytes(b"original")
        with patch.object(lumen.os, "replace", side_effect=PermissionError("permission denied")):
            with self.assertRaises(PermissionError):
                lumen.atomic_write(output, b"new")
        self.assertEqual(output.read_bytes(), b"original")
        self.assertEqual(list(self.root.glob(".lumen-*")), [])

    def test_disk_full_preserves_old_file(self):
        output = self.root / "result.patch"
        output.write_bytes(b"original")
        with patch.object(lumen.os, "fsync", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                lumen.atomic_write(output, b"new")
        self.assertEqual(output.read_bytes(), b"original")
        self.assertEqual(list(self.root.glob(".lumen-*")), [])

    def test_successful_replace(self):
        output = self.root / "result.patch"
        lumen.atomic_write(output, b"old")
        lumen.atomic_write(output, b"new")
        self.assertEqual(output.read_bytes(), b"new")

    def test_source_wrong_revision_rejected(self):
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Lumen tooling test",
                        "-c", "user.email=unused@example.invalid", "commit", "--quiet",
                        "--allow-empty", "-m", "Temporary fixture"], check=True)
        lock, delta = lumen.render_patch()
        with self.assertRaisesRegex(ValueError, "revision does not match"):
            lumen.check_source(self.root, lock, delta)

    def test_protected_output_rejected(self):
        before = (lumen.ROOT / "upstream.lock.json").read_bytes()
        self.assertEqual(lumen.main(["patch", "--output", str(lumen.ROOT / "upstream.lock.json")]), 2)
        self.assertEqual((lumen.ROOT / "upstream.lock.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
