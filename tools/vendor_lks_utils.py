"""
Bundle a slim lks_utils subset into the LKS cModule root.

Modes:
    --link    Create a Windows junction from lks_utils/ → live source
    --vendor  Remove junction, scan imports, copy only needed modules
    --status  Report current state (junction vs real files)
    --unlink  Remove the junction (restore to clean state)

Dev mode uses a junction at ``<LKS>/lks_utils`` so edits to the live
lks_utils source are immediately available.

Vendor (release) mode scans LKS production .py files for ``lks_utils``
imports, resolves transitive deps, and copies only those leaf modules
into ``<LKS>/lks_utils/`` as real files. Imports then work with **only**
the addon root on ``sys.path`` — no separate vendor path, no external
lks_utils location.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# --- Constants ---
_LKS_ROOT: Path = Path(__file__).parent.parent.resolve()
# Bundled package lives at addon root so ``import lks_utils`` works with
# only ``_LKS_ROOT`` on sys.path (see __onstartup.py).
_BUNDLE_LKS: Path = _LKS_ROOT / "lks_utils"
_LKS_UTILS_SRC: Path = Path("c:/BTS_SSD/Work_Scripts/lib/lks_utils/src/lks_utils")
_MANIFEST_FILE: Path = _BUNDLE_LKS / "_vendor_manifest.json"
_PKG_ROOT: str = "lks_utils"

# Skip these path parts when scanning LKS for imports
_SCAN_SKIP_PARTS: frozenset[str] = frozenset({
    "lks_utils",  # bundled copy / junction — do not scan as consumer code
    "vendor",  # legacy junction location
    "venv",
    ".venv",
    "__pycache__",
    ".git",
    ".cursor",
    ".docs",
    "_docs",
    "docs",
    "test",
    "tools",
    "_tools",
    ".tools",
    ".example_code",
    ".github",
    ".vscode",
    ".pytest_cache",
})

# Packages whose source __init__.py must never be copied (fat aggregators).
_FORCE_STUB_PACKAGES: frozenset[str] = frozenset({
    "lks_utils",
    "lks_utils.gui_qt",
    "lks_utils.gui_qt.widgets",
    "lks_utils.gui_qt.theme",
})

_FROM_IMPORT_RE: re.Pattern[str] = re.compile(
    r"^\s*from\s+(lks_utils(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\s+import\s+(.+)$",
    re.MULTILINE,
)
_IMPORT_MOD_RE: re.Pattern[str] = re.compile(
    r"^\s*import\s+(lks_utils(?:\.[A-Za-z_][A-Za-z0-9_]*)*)(?:\s+as\s+\w+)?\s*$",
    re.MULTILINE,
)
_EXPORT_FROM_REL_RE: re.Pattern[str] = re.compile(
    r"^\s*from\s+(\.[\w.]*)\s+import\s+(.+)$",
    re.MULTILINE,
)
_EXPORT_FROM_ABS_RE: re.Pattern[str] = re.compile(
    r"^\s*from\s+(lks_utils(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\s+import\s+(.+)$",
    re.MULTILINE,
)

_INVALID_FILE_ATTRIBUTES: int = 0xFFFFFFFF
_FILE_ATTRIBUTE_REPARSE_POINT: int = 0x400


def is_junction(path: Path) -> bool:
    """Check if path is a Windows directory junction (reparse point)."""
    if not path.exists():
        return False
    if os.name != "nt":
        return path.is_symlink()
    attrs: int = ctypes.windll.kernel32.GetFileAttributesW(str(path))
    if attrs == _INVALID_FILE_ATTRIBUTES:
        return False
    return bool(attrs & _FILE_ATTRIBUTE_REPARSE_POINT)


def _get_junction_target(path: Path) -> str | None:
    """Resolve a Windows junction target via dir /al."""
    if not is_junction(path):
        return None
    try:
        result = subprocess.run(
            ["cmd", "/c", "dir", "/al", str(path.parent)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        name: str = path.name
        for line in result.stdout.splitlines():
            if "JUNCTION" in line and name in line:
                match = re.search(r"\[(.*?)\]", line)
                if match:
                    return match.group(1)
        return str(_LKS_UTILS_SRC)
    except Exception:
        return str(_LKS_UTILS_SRC)


def _join_continuation_lines(content: str) -> str:
    """Join multi-line imports into single lines for regex matching."""
    content = re.sub(r"\\\s*\n\s*", " ", content)
    result_lines: list[str] = []
    buf: str = ""
    depth: int = 0
    for line in content.splitlines(keepends=False):
        if depth > 0:
            buf += " " + line.strip()
            depth += line.count("(") - line.count(")")
            if depth <= 0:
                result_lines.append(buf)
                buf = ""
            continue
        opens: int = line.count("(")
        closes: int = line.count(")")
        if opens > closes and (
            line.strip().startswith("from ") or line.strip().startswith("import ")
        ):
            depth = opens - closes
            buf = line.strip()
            if depth <= 0:
                result_lines.append(buf)
                buf = ""
        else:
            result_lines.append(line)
    if buf:
        result_lines.append(buf)
    return "\n".join(result_lines)


def _parse_import_names(names_blob: str) -> list[str]:
    """Parse ``a, b as c, (d, e)`` into exported names (original, not alias)."""
    cleaned: str = names_blob.strip()
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = cleaned[1:-1]
    names: list[str] = []
    for part in cleaned.split(","):
        part = part.strip()
        if not part or part == "*":
            continue
        name: str = part.split(" as ", 1)[0].strip()
        if name and name.isidentifier():
            names.append(name)
    return names


def _dotted_to_rel(mod_dotted: str) -> Path:
    """Convert ``lks_utils.gui_qt.widgets.x`` → ``gui_qt/widgets/x`` under src."""
    if mod_dotted == _PKG_ROOT:
        return Path()
    prefix: str = _PKG_ROOT + "."
    if not mod_dotted.startswith(prefix):
        raise ValueError(f"Not an lks_utils module: {mod_dotted}")
    return Path(mod_dotted[len(prefix):].replace(".", "/"))


def _src_path_for_module(mod_dotted: str) -> Path | None:
    """Return source file path for a module."""
    rel: Path = _dotted_to_rel(mod_dotted)
    if mod_dotted == _PKG_ROOT:
        init_file: Path = _LKS_UTILS_SRC / "__init__.py"
        return init_file if init_file.exists() else None
    as_file: Path = (_LKS_UTILS_SRC / rel).with_suffix(".py")
    if as_file.is_file():
        return as_file
    as_pkg: Path = _LKS_UTILS_SRC / rel / "__init__.py"
    if as_pkg.is_file():
        return as_pkg
    return None


def _is_package_module(mod_dotted: str) -> bool:
    """True if dotted path refers to a package (directory with __init__.py)."""
    rel: Path = _dotted_to_rel(mod_dotted)
    if mod_dotted == _PKG_ROOT:
        return (_LKS_UTILS_SRC / "__init__.py").is_file()
    return (_LKS_UTILS_SRC / rel / "__init__.py").is_file() and not (
        _LKS_UTILS_SRC / rel
    ).with_suffix(".py").is_file()


def _should_skip_scan_path(py_file: Path) -> bool:
    """Whether an LKS tree path should be ignored during import scan."""
    try:
        rel_parts: tuple[str, ...] = py_file.resolve().relative_to(_LKS_ROOT).parts
    except ValueError:
        return True
    if any(part in _SCAN_SKIP_PARTS for part in rel_parts):
        return True
    name: str = py_file.name
    if name.startswith("_test_") or name.endswith("_test.py"):
        return True
    return False


def _build_export_map(package_dotted: str) -> dict[str, str]:
    """Map export name → leaf module dotted path from a package ``__init__.py``."""
    init_path: Path | None = _src_path_for_module(package_dotted)
    if init_path is None:
        return {}
    try:
        content: str = _join_continuation_lines(init_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, PermissionError, OSError):
        return {}

    export_map: dict[str, str] = {}

    def _record(target_mod: str, names_blob: str) -> None:
        for name in _parse_import_names(names_blob):
            export_map.setdefault(name, target_mod)

    for match in _EXPORT_FROM_ABS_RE.finditer(content):
        _record(match.group(1), match.group(2))

    for match in _EXPORT_FROM_REL_RE.finditer(content):
        rel_mod: str = match.group(1)
        names_blob: str = match.group(2)
        level: int = 0
        for ch in rel_mod:
            if ch == ".":
                level += 1
            else:
                break
        remainder: str = rel_mod[level:]
        pkg_parts: list[str] = package_dotted.split(".")
        if level < 1 or level > len(pkg_parts):
            continue
        base: str = ".".join(pkg_parts[: len(pkg_parts) - (level - 1)])
        target = f"{base}.{remainder}" if remainder else base
        _record(target, names_blob)

    return export_map


def _parse_file_imports(content: str) -> list[tuple[str, list[str] | None]]:
    """Return list of (module, names|None) from file content."""
    joined: str = _join_continuation_lines(content)
    results: list[tuple[str, list[str] | None]] = []
    for match in _FROM_IMPORT_RE.finditer(joined):
        mod: str = match.group(1)
        names: list[str] = _parse_import_names(match.group(2))
        results.append((mod, names if names else None))
    for match in _IMPORT_MOD_RE.finditer(joined):
        results.append((match.group(1), None))
    return results


def _remove_bundle() -> None:
    """Remove existing lks_utils bundle (junction or real files)."""
    if not _BUNDLE_LKS.exists():
        return
    if is_junction(_BUNDLE_LKS):
        ctypes.windll.kernel32.RemoveDirectoryW(str(_BUNDLE_LKS))
    else:
        shutil.rmtree(str(_BUNDLE_LKS))


def cmd_link() -> None:
    """Create lks_utils/ junction pointing to live source."""
    legacy: Path = _LKS_ROOT / "vendor" / "lks_utils"
    if legacy.exists() and is_junction(legacy):
        ctypes.windll.kernel32.RemoveDirectoryW(str(legacy))
        print(f"[link] Removed legacy junction: {legacy}")

    if _BUNDLE_LKS.exists():
        if is_junction(_BUNDLE_LKS):
            print(f"[link] Junction already exists: {_BUNDLE_LKS}")
            target = _get_junction_target(_BUNDLE_LKS)
            if target:
                print(f"[link] Target: {target}")
            return
        print(f"[link] Removing existing real files at {_BUNDLE_LKS}")
        shutil.rmtree(str(_BUNDLE_LKS))
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(_BUNDLE_LKS), str(_LKS_UTILS_SRC)],
        check=True,
    )
    print(f"[link] Created junction: {_BUNDLE_LKS} -> {_LKS_UTILS_SRC}")
    print("[link] Dev mode active — edits to lks_utils source are live.")


def scan_imports(root: Path) -> dict[str, set[str]]:
    """Scan production .py files for lks_utils imports."""
    needed: dict[str, set[str]] = {}
    py_files: list[Path] = list(root.rglob("*.py"))
    scanned: int = 0
    for py_file in py_files:
        if _should_skip_scan_path(py_file):
            continue
        scanned += 1
        try:
            content: str = py_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError, OSError):
            continue
        for mod, names in _parse_file_imports(content):
            bucket: set[str] = needed.setdefault(mod, set())
            if names:
                bucket.update(names)
    print(f"[vendor] Scanned {scanned} production .py files in LKS/")
    return needed


def resolve_transitive(
    top_level: dict[str, set[str]],
) -> tuple[set[str], dict[str, set[str]]]:
    """Resolve transitive leaf modules and package re-export requirements."""
    resolved: set[str] = set()
    package_exports: dict[str, set[str]] = {}
    queue: list[tuple[str, list[str] | None]] = [
        (mod, sorted(names) if names else None)
        for mod, names in top_level.items()
    ]

    while queue:
        mod_dotted, names = queue.pop()
        if mod_dotted in resolved and not names:
            continue

        src: Path | None = _src_path_for_module(mod_dotted)
        if src is None:
            print(f"[vendor] WARNING: missing module {mod_dotted}")
            continue

        is_pkg: bool = _is_package_module(mod_dotted)

        if is_pkg and names:
            package_exports.setdefault(mod_dotted, set()).update(names)
            export_map: dict[str, str] = _build_export_map(mod_dotted)
            for name in names:
                target: str | None = export_map.get(name)
                if target is None:
                    guess: str = f"{mod_dotted}.{_camel_to_snake(name)}"
                    if _src_path_for_module(guess) is not None:
                        target = guess
                if target is None:
                    print(
                        f"[vendor] WARNING: cannot resolve {name!r} from {mod_dotted}"
                    )
                    continue
                if target not in resolved:
                    queue.append((target, None))
            resolved.add(mod_dotted)
            continue

        if is_pkg and mod_dotted in _FORCE_STUB_PACKAGES:
            resolved.add(mod_dotted)
            continue

        if is_pkg:
            resolved.add(mod_dotted)
            try:
                content = src.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError, OSError):
                continue
            for inner_mod, inner_names in _parse_file_imports(content):
                if inner_mod not in resolved or inner_names:
                    queue.append((inner_mod, inner_names))
            continue

        if mod_dotted in resolved:
            continue
        resolved.add(mod_dotted)
        try:
            content = src.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError, OSError):
            continue
        for inner_mod, inner_names in _parse_file_imports(content):
            if inner_mod not in resolved or inner_names:
                queue.append((inner_mod, inner_names))

    return resolved, package_exports


def _camel_to_snake(name: str) -> str:
    """Best-effort CamelCase / QFoo → snake for module guess."""
    if name.startswith("Q") and len(name) > 1 and name[1].isupper():
        name = name[1:]
    spaced: str = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", spaced).lower()


def _ensure_package_stub(
    package_dotted: str,
    exports: dict[str, set[str]],
    export_maps_cache: dict[str, dict[str, str]],
    copied: set[str],
) -> None:
    """Write a slim ``__init__.py`` with lazy re-exports under bundled lks_utils."""
    rel: Path = _dotted_to_rel(package_dotted)
    dest_init: Path = (
        _BUNDLE_LKS / "__init__.py"
        if package_dotted == _PKG_ROOT
        else _BUNDLE_LKS / rel / "__init__.py"
    )
    dest_init.parent.mkdir(parents=True, exist_ok=True)

    names: set[str] = set(exports.get(package_dotted, set()))
    force_stub: bool = package_dotted in _FORCE_STUB_PACKAGES or bool(names)

    src_init: Path | None = _src_path_for_module(package_dotted)
    if not force_stub and src_init is not None:
        try:
            src_text: str = src_init.read_text(encoding="utf-8")
            if _parse_file_imports(src_text):
                force_stub = True
        except (UnicodeDecodeError, PermissionError, OSError):
            force_stub = True

    if force_stub:
        lines: list[str] = [
            f'"""Slim bundled stub for {package_dotted} (LKS release)."""',
            "from __future__ import annotations",
            "",
        ]
        if package_dotted == _PKG_ROOT:
            lines.extend(['__version__ = "0.1.0-bundled"', ""])

        if names:
            if package_dotted not in export_maps_cache:
                export_maps_cache[package_dotted] = _build_export_map(package_dotted)
            export_map = export_maps_cache[package_dotted]
            export_pairs: list[tuple[str, str]] = []
            for name in sorted(names):
                target = export_map.get(name)
                if target is None:
                    lines.append(f"# unresolved export: {name}")
                    continue
                export_pairs.append((name, target))
            lines.append("from typing import Any")
            lines.append("import importlib")
            lines.append("")
            lines.append("_LAZY_EXPORTS: dict[str, str] = {")
            for name, target in export_pairs:
                lines.append(f"    {name!r}: {target!r},")
            lines.append("}")
            lines.append("")
            lines.append(f"__all__ = {sorted(n for n, _ in export_pairs)!r}")
            lines.append("")
            lines.append("def __getattr__(name: str) -> Any:")
            lines.append("    mod_path = _LAZY_EXPORTS.get(name)")
            lines.append("    if mod_path is None:")
            lines.append(
                f"        raise AttributeError(f\"module {package_dotted!r} \"")
            lines.append("            f\"has no attribute {name!r}\")")
            lines.append("    mod = importlib.import_module(mod_path)")
            lines.append("    value = getattr(mod, name)")
            lines.append("    globals()[name] = value")
            lines.append("    return value")
            lines.append("")
        else:
            lines.append("__all__: list[str] = []")
            lines.append("")

        dest_init.write_text("\n".join(lines), encoding="utf-8")
        copied.add(str(dest_init.relative_to(_BUNDLE_LKS)).replace("\\", "/"))
        return

    if src_init is not None:
        shutil.copy2(str(src_init), str(dest_init))
    else:
        dest_init.write_text(
            f'"""Slim bundled stub for {package_dotted}."""\n'
            "from __future__ import annotations\n",
            encoding="utf-8",
        )
    copied.add(str(dest_init.relative_to(_BUNDLE_LKS)).replace("\\", "/"))


def _copy_package_resource_dirs(
    modules: set[str],
    copied: set[str],
) -> None:
    """Copy ``data/`` / ``resources/`` folders next to bundled packages.

    Leaf ``.py`` modules often load sibling resource trees via
    ``Path(__file__).parent / "data"`` (e.g. theme builtins, button icons).
    """
    resource_names: frozenset[str] = frozenset({"data", "resources"})
    package_dirs: set[Path] = set()
    for mod_dotted in modules:
        rel: Path = _dotted_to_rel(mod_dotted)
        if mod_dotted == _PKG_ROOT:
            package_dirs.add(_LKS_UTILS_SRC)
            continue
        if _is_package_module(mod_dotted):
            package_dirs.add(_LKS_UTILS_SRC / rel)
        else:
            package_dirs.add((_LKS_UTILS_SRC / rel).parent)

    for pkg_dir in sorted(package_dirs):
        if not pkg_dir.is_dir():
            continue
        # Never pull test fixture trees
        try:
            rel_pkg = pkg_dir.relative_to(_LKS_UTILS_SRC)
        except ValueError:
            continue
        if "test" in rel_pkg.parts:
            continue
        for res_name in resource_names:
            data_src: Path = pkg_dir / res_name
            if not data_src.is_dir():
                continue
            data_dst: Path = _BUNDLE_LKS / rel_pkg / res_name
            if data_dst.exists():
                continue
            shutil.copytree(
                str(data_src),
                str(data_dst),
                ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", ".vscode", "test", "tests",
                ),
            )
            n_files: int = 0
            for f in data_dst.rglob("*"):
                if f.is_file():
                    copied.add(
                        str(f.relative_to(_BUNDLE_LKS)).replace("\\", "/")
                    )
                    n_files += 1
            print(
                f"[vendor] + package resources: {rel_pkg.as_posix()}/{res_name}/ "
                f"({n_files} files)"
            )


def copy_modules(
    modules: set[str],
    package_exports: dict[str, set[str]],
) -> None:
    """Copy leaf modules and write slim package stubs into lks_utils/."""
    _remove_bundle()
    _BUNDLE_LKS.mkdir(parents=True)

    copied: set[str] = set()
    export_maps_cache: dict[str, dict[str, str]] = {}

    for mod_dotted in sorted(modules):
        if _is_package_module(mod_dotted):
            continue
        src: Path | None = _src_path_for_module(mod_dotted)
        if src is None:
            continue
        rel: Path = _dotted_to_rel(mod_dotted).with_suffix(".py")
        dest: Path = _BUNDLE_LKS / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dest))
        copied.add(str(rel).replace("\\", "/"))

        for sibling in src.parent.iterdir():
            if not sibling.is_file():
                continue
            if sibling.suffix.lower() not in {
                ".svg", ".qss", ".json", ".md", ".txt", ".png", ".ico",
            }:
                continue
            parent_name: str = src.parent.name
            if parent_name.startswith("_") or sibling.stem == src.stem:
                sib_dest: Path = dest.parent / sibling.name
                if not sib_dest.exists():
                    shutil.copy2(str(sibling), str(sib_dest))
                    copied.add(
                        str(sib_dest.relative_to(_BUNDLE_LKS)).replace("\\", "/")
                    )

    packages_needed: set[str] = set(package_exports.keys()) | set(_FORCE_STUB_PACKAGES)
    for mod_dotted in modules:
        parts: list[str] = mod_dotted.split(".")
        for i in range(1, len(parts) + (1 if _is_package_module(mod_dotted) else 0)):
            packages_needed.add(".".join(parts[:i]))

    for package_dotted in sorted(packages_needed, key=lambda s: s.count(".")):
        _ensure_package_stub(package_dotted, package_exports, export_maps_cache, copied)

    _copy_package_resource_dirs(modules, copied)

    py_typed_src: Path = _LKS_UTILS_SRC / "py.typed"
    if py_typed_src.exists():
        shutil.copy2(str(py_typed_src), str(_BUNDLE_LKS / "py.typed"))
        copied.add("py.typed")

    manifest: dict[str, object] = {
        "source": str(_LKS_UTILS_SRC),
        "bundled_at": datetime.now().isoformat(),
        "modules": sorted(modules),
        "package_exports": {
            k: sorted(v) for k, v in sorted(package_exports.items())
        },
        "file_count": len(copied),
        "files": sorted(copied),
    }
    _MANIFEST_FILE.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    copied.add("_vendor_manifest.json")

    print(f"[vendor] Copied {len(copied)} files for {len(modules)} modules")
    print(f"[vendor] Manifest: {_MANIFEST_FILE}")


def cmd_vendor() -> None:
    """Scan imports, resolve transitive deps, copy needed modules."""
    if not _LKS_UTILS_SRC.exists():
        print(f"[vendor] ERROR: lks_utils source not found at {_LKS_UTILS_SRC}")
        raise SystemExit(1)
    print("[vendor] Scanning imports...")
    top_level: dict[str, set[str]] = scan_imports(_LKS_ROOT)
    print(f"[vendor] Found {len(top_level)} top-level lks_utils imports")
    for mod in sorted(top_level):
        names = top_level[mod]
        suffix = f"  ({', '.join(sorted(names))})" if names else ""
        print(f"  {mod}{suffix}")
    resolved, package_exports = resolve_transitive(top_level)
    print(f"[vendor] Resolved {len(resolved)} modules (with transitive deps)")
    for mod in sorted(resolved):
        marker = "  (root)" if mod in top_level else "  (trans)"
        print(f"  {mod}{marker}")
    if package_exports:
        print("[vendor] Package stub re-exports:")
        for pkg, names in sorted(package_exports.items()):
            print(f"  {pkg}: {', '.join(sorted(names))}")
    copy_modules(resolved, package_exports)
    total_bytes: int = sum(
        f.stat().st_size for f in _BUNDLE_LKS.rglob("*") if f.is_file()
    )
    print(f"[vendor] Bundle size: {total_bytes / 1024:.1f} KB")
    print("[vendor] Bundled at addon root: lks_utils/ (import via LKS root only).")


def cmd_status() -> None:
    """Report current state of bundled lks_utils/."""
    if not _BUNDLE_LKS.exists():
        print("[status] lks_utils/ does not exist.")
        print("[status] Run 'python tools/vendor_lks_utils.py --link' to create junction.")
        return
    if is_junction(_BUNDLE_LKS):
        target: str | None = _get_junction_target(_BUNDLE_LKS)
        if target:
            print(f"[status] JUNCTION: lks_utils/ -> {target}")
        else:
            print("[status] JUNCTION: lks_utils/ (target unknown)")
    else:
        py_count: int = len(list(_BUNDLE_LKS.rglob("*.py")))
        total_bytes: int = sum(
            f.stat().st_size for f in _BUNDLE_LKS.rglob("*") if f.is_file()
        )
        print(
            f"[status] REAL FILES: lks_utils/ "
            f"({py_count} .py files, {total_bytes / 1024:.1f} KB)"
        )
        if _MANIFEST_FILE.exists():
            try:
                manifest: dict = json.loads(_MANIFEST_FILE.read_text(encoding="utf-8"))
                print(
                    f"[status] Bundled at: "
                    f"{manifest.get('bundled_at', manifest.get('vendored_at', 'unknown'))}"
                )
                print(f"[status] Modules: {len(manifest.get('modules', []))}")
            except (json.JSONDecodeError, KeyError):
                print("[status] Manifest exists but is unreadable.")


def cmd_unlink() -> None:
    """Remove lks_utils/ (junction or real files)."""
    if not _BUNDLE_LKS.exists():
        print("[unlink] Nothing to remove.")
        return
    _remove_bundle()
    print("[unlink] Removed lks_utils/ bundle.")


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Bundle slim lks_utils into LKS cModule root"
    )
    parser.add_argument("--link", action="store_true", help="Create junction to live source")
    parser.add_argument("--vendor", action="store_true", help="Copy only imported modules")
    parser.add_argument("--status", action="store_true", help="Show current state")
    parser.add_argument("--unlink", action="store_true", help="Remove junction/bundled files")
    args: argparse.Namespace = parser.parse_args()

    if args.link:
        cmd_link()
    elif args.vendor:
        cmd_vendor()
    elif args.status:
        cmd_status()
    elif args.unlink:
        cmd_unlink()
    else:
        parser.print_help()
