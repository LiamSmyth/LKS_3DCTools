"""Sandbox: pack slim lks_utils and verify imports with only addon root on path.

Simulates a released .zip/.3dcpack install:
1. Bundle slim lks_utils into the LKS tree
2. Copy a minimal sandbox tree (no junction, no Work_Scripts path)
3. Import critical modules with ONLY the sandbox root on sys.path
4. Assert no sys.path entry points at the external lks_utils source
5. Restore the dev junction

Exit 0 on success, 1 on failure.
"""
from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path

_LKS_ROOT: Path = Path(__file__).resolve().parents[1]
_EXTERNAL_SRC: str = "c:/BTS_SSD/Work_Scripts/lib/lks_utils"
_SANDBOX: Path = _LKS_ROOT / "_pack_probe_sandbox" / "LKS_ImportProbe"

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

# Top-level LKS packages needed so utils.ui.styles can resolve if we import it
_COPY_TOP: list[str] = [
    "lks_utils",
    "__onstartup.py",
]


def _load_vendor_mod():  # type: ignore[no-untyped-def]
    import importlib.util

    script = _LKS_ROOT / "tools" / "vendor_lks_utils.py"
    spec = importlib.util.spec_from_file_location("lks_vendor_probe", script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _assert_no_external_on_path() -> None:
    external_norm = str(Path(_EXTERNAL_SRC).resolve()).lower().replace("\\", "/")
    for entry in sys.path:
        if not entry:
            continue
        norm = str(Path(entry).resolve()).lower().replace("\\", "/")
        if external_norm in norm or norm.endswith("/lib/lks_utils") or "/lib/lks_utils/src" in norm:
            raise AssertionError(f"External lks_utils on sys.path: {entry}")


def main() -> int:
    vendor = _load_vendor_mod()
    print("[probe] Bundling slim lks_utils...")
    vendor.cmd_vendor()

    if vendor.is_junction(_LKS_ROOT / "lks_utils"):
        print("[probe] FAIL: lks_utils is still a junction after --vendor")
        return 1

    # Build isolated sandbox containing only the bundled tree pieces we need
    if _SANDBOX.exists():
        shutil.rmtree(_SANDBOX)
    _SANDBOX.mkdir(parents=True)

    src_bundle = _LKS_ROOT / "lks_utils"
    dst_bundle = _SANDBOX / "lks_utils"
    shutil.copytree(src_bundle, dst_bundle)
    shutil.copy2(_LKS_ROOT / "__onstartup.py", _SANDBOX / "__onstartup.py")

    # Clear any cached lks_utils modules from this process
    for key in list(sys.modules):
        if key == "lks_utils" or key.startswith("lks_utils."):
            del sys.modules[key]

    # Isolate path: keep stdlib/site-packages, drop any LKS / external lks_utils
    # entries, then put ONLY the sandbox addon root first.
    saved_path = list(sys.path)
    cleaned: list[str] = []
    lks_norm = str(_LKS_ROOT.resolve()).lower().replace("\\", "/")
    external_norm = str(Path(_EXTERNAL_SRC).resolve()).lower().replace("\\", "/")
    for entry in sys.path:
        if not entry:
            cleaned.append(entry)
            continue
        try:
            norm = str(Path(entry).resolve()).lower().replace("\\", "/")
        except OSError:
            cleaned.append(entry)
            continue
        if norm.startswith(lks_norm) or external_norm in norm:
            continue
        if "/cExtensions/LKS" in norm.replace("\\", "/"):
            continue
        cleaned.append(entry)
    sys.path[:] = [str(_SANDBOX)] + cleaned
    try:
        _assert_no_external_on_path()

        # Simulate __onstartup path setup (addon root only)
        onstartup = (_SANDBOX / "__onstartup.py").read_text(encoding="utf-8")
        for line in onstartup.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "vendor" in stripped and "sys.path" in stripped:
                raise AssertionError(
                    f"__onstartup still adds vendor to sys.path: {stripped}"
                )

        print("[probe] Importing critical modules (sandbox root only)...")
        for mod_name in _CRITICAL_IMPORTS:
            importlib.import_module(mod_name)
            print(f"  OK  {mod_name}")

        # Lazy package re-exports
        from lks_utils.gui_qt.theme import ThemeAwareMixin  # noqa: F401
        from lks_utils.core import atomic_write  # noqa: F401
        print("  OK  lazy ThemeAwareMixin / atomic_write")

        # Builtin theme JSON resources must ship with theme_io
        theme_data = _SANDBOX / "lks_utils" / "theme" / "data"
        if not theme_data.is_dir():
            raise AssertionError(f"Missing bundled theme data dir: {theme_data}")
        from lks_utils.theme.theme_io import load_builtin_themes

        themes = load_builtin_themes()
        if len(themes) < 1:
            raise AssertionError("load_builtin_themes() returned empty list")
        print(f"  OK  load_builtin_themes ({len(themes)} themes)")

        import lks_utils

        loaded_file = Path(lks_utils.__file__).resolve()
        sandbox_norm = str(_SANDBOX.resolve()).lower().replace("\\", "/")
        loaded_norm = str(loaded_file).lower().replace("\\", "/")
        if not loaded_norm.startswith(sandbox_norm):
            raise AssertionError(
                f"lks_utils loaded from outside sandbox: {loaded_file}"
            )
        print(f"[probe] lks_utils.__file__ = {loaded_file}")

        _assert_no_external_on_path()
        print("[probe] PASS — imports work with only addon root on sys.path")
        ok = True
    except Exception as exc:
        print(f"[probe] FAIL: {exc}")
        ok = False
    finally:
        sys.path[:] = saved_path
        for key in list(sys.modules):
            if key == "lks_utils" or key.startswith("lks_utils."):
                del sys.modules[key]
        print("[probe] Restoring lks_utils/ junction...")
        vendor.cmd_link()

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
