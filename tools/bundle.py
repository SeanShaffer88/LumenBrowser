"""SPDX-License-Identifier: MPL-2.0. Reproducible source bundle, not a browser installer."""
import argparse
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

import lumen


def source_bundle(root=lumen.ROOT):
    root = Path(root).resolve()
    lock, patch = lumen.render_patch(root)
    paths = set()
    paths.update(root.glob("*.md"))
    paths.update(root / name for name in ("LICENSE", ".gitignore", ".gitattributes", "upstream.lock.json"))
    for folder in ("config", "tools", "tests", "docs", "browser", "benchmarks", "branding", ".github"):
        paths.update(p for p in (root / folder).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    paths.update(root / "audit/upstream" / e["path"] for e in lock["files"])
    entries = {}
    for path in sorted(paths):
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f"Bundle input is a link or escapes repository: {path}")
        entries[path.relative_to(root).as_posix()] = path.read_bytes()
    entries["patches/lumen.patch"] = patch.encode("utf-8")
    entries["MANIFEST.sha256"] = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(entries.items())
    ).encode("utf-8")
    stamp = date.fromisoformat(lock["retrieved_utc"])
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(entries.items()):
            entry = zipfile.ZipInfo(f"LumenBrowser/{name}", (stamp.year, stamp.month, stamp.day, 0, 0, 0))
            entry.create_system = 3
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    return result.getvalue()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if not args.output.resolve().is_relative_to(lumen.ROOT / "out"):
            raise ValueError("Bundle output must be under repository out/")
        data = source_bundle()
        lumen.atomic_write(args.output, data)
        print(json.dumps({"status": "ok", "sha256": hashlib.sha256(data).hexdigest(),
                          "bytes": len(data), "browser_built": False}))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"lumen-bundle: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
