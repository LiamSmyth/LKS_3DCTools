"""Sandbox: verify slim lks_utils imports with only the addon root on path.

Simulates a released .zip/.3dcpack install:
1. Optionally bundle slim lks_utils into the LKS tree
2. Copy / use an isolated tree (no junction, no Work_Scripts path)
3. Import every vendored module with ONLY that addon root on sys.path
4. Assert lks_utils.__file__ is under the sandbox (not external source)
5. Optionally restore the dev junction

Never consults env vars for lks_utils location during the import phase —
clearing PYTHONPATH / LKS_UTILS* avoids false passes from external code.

Exit 0 on success, 1 on failure.

Usage:
    python tools/probe_bundled_imports.py
    python tools/probe_bundled_imports.py --addon-root path/to/extracted/LKS_Side
    python tools/probe_bundled_imports.py --skip-vendor --no-restore
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import sys
from pathlib import Path

_LKS_ROOT: Path = Path(__file__).resolve().parents[1]
_EXTERNAL_SRC: Path = Path("c:/BTS_SSD/Work_Scripts/lib/lks_utils")
_SANDBOX: Path = _LKS_ROOT / "_pack_probe_sandbox" / "LKS_ImportProbe"

# Hard ceiling — slim bundle is ~0.5 MB; anything near the fat repo is a bug.
_MAX_BUNDLE_BYTES: int = 10 * 1024 * 1024

_ENV_KEYS_TO_CLEAR: tuple[str, ...] = (
    "PYTHONPATH",
    "LKS_UTILS_SRC",
    "LKS_UTILS_ROOT",
    "LKS_UTILS_PATH",
)

_CRITICAL_IMPORTS: list[str] = [
    "lks_utils.gui_qt.theme.dark_theme",
    "lks_utils.gui_qt.theme.colors",
    "lks_utils.gui_qt.widgets.activity_log",
    "lks_utils.gui_qt.widgets.enhanced_slider",
    "lks_utils.gui_qt.widgets.q_dial_enum_picker",
    "lks_utils.gui_qt.widgets.collapsible_section",
    "lks_utils.gui_qt.widgets.tooltip",
    "lks_utils.gui_qt.widgets.smooth_scroll_area",
    "lks_utils.gui_qt.widgets.badge_button",
    "lks_utils.gui_qt.widgets.tab_widget",
    "lks_utils.gui_qt.widgets.embedded_dialog",
    "lks_utils.gui_qt.widgets.svg_icon_picker",
    "lks_utils.gui_qt.widgets.grip_box_container",
    "lks_utils.gui_qt.widgets.save_load_library",
    "lks_utils.input",
    "lks_utils.theme.theme",
]


def _load_vendor_mod():  # type: ignore[no-untyped-def]
    import importlib.util

    script = _LKS_ROOT / "tools" / "vendor_lks_utils.py"
    spec = importlib.util.spec_from_file_location("lks_vendor_probe", script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _norm(path: Path | str) -> str:
    return str(Path(path).resolve()).lower().replace("\\", "/")


def assert_no_junctions(root: Path) -> None:
    """Fail if ``root`` or any subdirectory is a Windows junction/symlink."""
    vendor = _load_vendor_mod()
    if not root.exists():
        raise AssertionError(f"Missing path: {root}")
    if vendor.is_junction(root):
        raise AssertionError(f"Junction not allowed in packaged tree: {root}")
    for dirpath, dirnames, _filenames in os.walk(root):
        current = Path(dirpath)
        # Check each child dir (os.walk follows junctions by default on Windows
        # unless we prune — detect before descending).
        for name in list(dirnames):
            child = current / name
            if vendor.is_junction(child):
                raise AssertionError(
                    f"Junction not allowed in packaged tree: {child}"
                )


def assert_bundle_size_ok(bundle: Path, max_bytes: int = _MAX_BUNDLE_BYTES) -> int:
    """Fail if slim bundle looks like the full fat repo."""
    total: int = sum(f.stat().st_size for f in bundle.rglob("*") if f.is_file())
    if total > max_bytes:
        raise AssertionError(
            f"lks_utils bundle too large ({total / (1024 * 1024):.1f} MB) — "
            f"likely included the full repo (limit {max_bytes / (1024 * 1024):.0f} MB)"
        )
    return total


def _modules_from_manifest(bundle: Path) -> list[str]:
    manifest_path = bundle / "_vendor_manifest.json"
    if not manifest_path.is_file():
        return list(_CRITICAL_IMPORTS)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    modules = data.get("modules")
    if not isinstance(modules, list) or not modules:
        return list(_CRITICAL_IMPORTS)
    names: list[str] = []
    for entry in modules:
        if isinstance(entry, str):
            names.append(entry)
        elif isinstance(entry, dict) and "name" in entry:
            names.append(str(entry["name"]))
    # Always include critical list even if older manifests omit some
    for name in _CRITICAL_IMPORTS:
        if name not in names:
            names.append(name)
    return names


def _purge_lks_utils_modules() -> None:
    for key in list(sys.modules):
        if key == "lks_utils" or key.startswith("lks_utils."):
            del sys.modules[key]


def _scrub_sys_path(addon_root: Path, external_src: Path) -> list[str]:
    """Return a cleaned sys.path with only addon_root prepended."""
    cleaned: list[str] = []
    addon_norm = _norm(addon_root)
    external_norm = _norm(external_src)
    lks_norm = _norm(_LKS_ROOT)
    for entry in sys.path:
        if not entry:
            cleaned.append(entry)
            continue
        try:
            norm = _norm(entry)
        except OSError:
            cleaned.append(entry)
            continue
        # Drop live LKS tree and external fat lks_utils; keep stdlib/site-packages.
        if norm.startswith(lks_norm):
            continue
        if external_norm in norm or "/lib/lks_utils" in norm:
            continue
        if "/cextensions/lks" in norm and not norm.startswith(addon_norm):
            continue
        cleaned.append(entry)
    return [str(addon_root.resolve())] + cleaned


def _assert_no_external_on_path(external_src: Path) -> None:
    external_norm = _norm(external_src)
    for entry in sys.path:
        if not entry:
            continue
        norm = _norm(entry)
        if external_norm in norm or "/lib/lks_utils" in norm:
            raise AssertionError(f"External lks_utils on sys.path: {entry}")


def probe_addon_root(
    addon_root: Path,
    *,
    external_src: Path = _EXTERNAL_SRC,
    clear_env: bool = True,
) -> None:
    """Import-probe an already-built addon tree. Raises on failure.

    Args:
        addon_root: Directory that contains ``lks_utils/`` (packaged tree).
        external_src: Path that must NOT appear on sys.path or in __file__.
        clear_env: Temporarily clear PYTHONPATH / LKS_UTILS* for the probe.
    """
    addon_root = addon_root.resolve()
    bundle = addon_root / "lks_utils"
    if not bundle.is_dir():
        raise AssertionError(f"Missing lks_utils/ under {addon_root}")

    assert_no_junctions(bundle)
    size = assert_bundle_size_ok(bundle)
    print(f"[probe] Bundle size OK: {size / 1024:.1f} KB under {bundle}")

    saved_env: dict[str, str | None] = {}
    if clear_env:
        for key in _ENV_KEYS_TO_CLEAR:
            saved_env[key] = os.environ.pop(key, None)

    saved_path = list(sys.path)
    _purge_lks_utils_modules()
    sys.path[:] = _scrub_sys_path(addon_root, external_src)

    try:
        _assert_no_external_on_path(external_src)

        onstartup = addon_root / "__onstartup.py"
        if onstartup.is_file():
            text = onstartup.read_text(encoding="utf-8")
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "vendor" in stripped and "sys.path" in stripped:
                    raise AssertionError(
                        f"__onstartup still adds vendor to sys.path: {stripped}"
                    )
                if "environ" in stripped and "sys.path" in stripped:
                    raise AssertionError(
                        f"__onstartup must not use env for sys.path: {stripped}"
                    )

        modules = _modules_from_manifest(bundle)
        print(f"[probe] Importing {len(modules)} modules (sandbox root only)...")
        for mod_name in modules:
            importlib.import_module(mod_name)
            print(f"  OK  {mod_name}")

        from lks_utils.gui_qt.theme import ThemeAwareMixin  # noqa: F401
        from lks_utils.core import atomic_write  # noqa: F401
        print("  OK  lazy ThemeAwareMixin / atomic_write")

        theme_data = bundle / "theme" / "data"
        if not theme_data.is_dir():
            raise AssertionError(f"Missing bundled theme data dir: {theme_data}")
        from lks_utils.theme.theme_io import load_builtin_themes

        themes = load_builtin_themes()
        if len(themes) < 1:
            raise AssertionError("load_builtin_themes() returned empty list")
        print(f"  OK  load_builtin_themes ({len(themes)} themes)")

        import lks_utils

        loaded_file = Path(lks_utils.__file__).resolve()
        if not _norm(loaded_file).startswith(_norm(addon_root)):
            raise AssertionError(
                f"lks_utils loaded from outside sandbox: {loaded_file}"
            )
        if _norm(external_src) in _norm(loaded_file):
            raise AssertionError(
                f"lks_utils resolved to external source: {loaded_file}"
            )
        print(f"[probe] lks_utils.__file__ = {loaded_file}")
        _assert_no_external_on_path(external_src)
        print("[probe] PASS - imports work with only addon root on sys.path")
    finally:
        sys.path[:] = saved_path
        _purge_lks_utils_modules()
        if clear_env:
            for key, value in saved_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


def build_default_sandbox_from_vendor() -> Path:
    """Copy vendored lks_utils + __onstartup into the default probe sandbox."""
    if _SANDBOX.exists():
        shutil.rmtree(_SANDBOX)
    _SANDBOX.mkdir(parents=True)
    shutil.copytree(_LKS_ROOT / "lks_utils", _SANDBOX / "lks_utils")
    shutil.copy2(_LKS_ROOT / "__onstartup.py", _SANDBOX / "__onstartup.py")
    return _SANDBOX


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Probe packaged lks_utils imports in an isolated sandbox"
    )
    parser.add_argument(
        "--addon-root",
        type=str,
        default=None,
        help="Existing packaged addon root to probe (skips sandbox copy)",
    )
    parser.add_argument(
        "--skip-vendor",
        action="store_true",
        help="Do not run --vendor (use existing real lks_utils/ files)",
    )
    parser.add_argument(
        "--no-restore",
        action="store_true",
        help="Do not restore the lks_utils/ junction afterward",
    )
    args = parser.parse_args(argv)

    vendor = _load_vendor_mod()
    did_vendor = False
    ok = False

    try:
        if args.addon_root:
            probe_addon_root(Path(args.addon_root))
            ok = True
        else:
            if not args.skip_vendor:
                print("[probe] Bundling slim lks_utils...")
                vendor.cmd_vendor()
                did_vendor = True

            bundle = _LKS_ROOT / "lks_utils"
            if vendor.is_junction(bundle):
                print("[probe] FAIL: lks_utils is still a junction after --vendor")
                return 1

            sandbox = build_default_sandbox_from_vendor()
            probe_addon_root(sandbox)
            ok = True
    except Exception as exc:
        print(f"[probe] FAIL: {exc}")
        ok = False
    finally:
        if did_vendor and not args.no_restore and not args.addon_root:
            print("[probe] Restoring lks_utils/ junction...")
            vendor.cmd_link()

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
