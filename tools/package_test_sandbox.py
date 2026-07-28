"""Build a side-install test .3dcpack with isolated import verification.

Flow:
1. Vendor slim ``lks_utils/`` (real files, no junction)
2. Assert bundle is small + junction-free
3. Pure-Python import probe with ONLY a sandbox addon root on sys.path
   (clears PYTHONPATH / LKS_UTILS* so external code cannot leak in)
4. Create ``--ext-name`` .3dcpack (neveruses overwriting live ``LKS``)
5. Extract the .3dcpack and re-probe the exact shipped tree
6. Optionally copy into ``cExtensions/<ExtName>/`` for live 3DCoat testing
7. Always restore the local ``lks_utils/`` junction afterward

Usage:
    python tools/package_test_sandbox.py --ext-name LKS_TestSandbox
    python tools/package_test_sandbox.py --ext-name LKS_Side --install-local --force
"""
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

_LKS_ROOT: Path = Path(__file__).resolve().parents[1]
_DEFAULT_EXT: str = "LKS_TestSandbox"
_FORBIDDEN_EXT: str = "LKS"


def _load_module(name: str, path: Path):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_vendor():  # type: ignore[no-untyped-def]
    return _load_module(
        "lks_vendor_for_sandbox",
        _LKS_ROOT / "tools" / "vendor_lks_utils.py",
    )


def _load_probe():  # type: ignore[no-untyped-def]
    return _load_module(
        "lks_probe_for_sandbox",
        _LKS_ROOT / "tools" / "probe_bundled_imports.py",
    )


def _load_package_release():  # type: ignore[no-untyped-def]
    return _load_module(
        "lks_package_release_for_sandbox",
        _LKS_ROOT / "package_release.py",
    )


def _validate_side_ext_name(name: str) -> str:
    pkg = _load_package_release()
    validated: str = pkg.validate_ext_name(name)
    if validated.upper() == _FORBIDDEN_EXT.upper():
        raise ValueError(
            f"Refusing ext-name {_FORBIDDEN_EXT!r} — that is the live development "
            f"addon. Use e.g. LKS_Side or LKS_TestSandbox."
        )
    return validated


def _run_pack_subprocess(
    ext_name: str,
    *,
    install_local: bool,
    force: bool,
    version: str | None,
) -> Path:
    """Invoke package_release with already-vendored tree; return .3dcpack path."""
    cmd: list[str] = [
        sys.executable,
        str(_LKS_ROOT / "package_release.py"),
        "--ext-name",
        ext_name,
        "--pack-only",
        "--skip-vendor",
        "--keep-vendored",
    ]
    if version:
        cmd.extend(["--version", version])
    if install_local:
        cmd.append("--install-local")
        if force:
            cmd.append("--force")

    print()
    print("=" * 60)
    print(" Creating .3dcpack (slim lks_utils already vendored)")
    print("=" * 60)
    print(f"  cmd: {' '.join(cmd)}")
    print()
    result = subprocess.run(cmd, cwd=str(_LKS_ROOT))
    if result.returncode != 0:
        raise RuntimeError(f"package_release.py failed (exit {result.returncode})")

    pkg = _load_package_release()
    output_dir = _LKS_ROOT.parent
    pack_path = output_dir / f"{pkg.artifact_basename(ext_name, version)}.3dcpack"
    if not pack_path.is_file():
        # Timestamp may have rolled — pick newest matching pack
        matches = sorted(
            output_dir.glob(f"{ext_name}_3DCoat_cModule_*.3dcpack"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not matches:
            raise FileNotFoundError(f"Expected .3dcpack not found under {output_dir}")
        pack_path = matches[0]
    return pack_path


def _extract_pack_addon_root(pack_path: Path, extract_dir: Path, ext_name: str) -> Path:
    """Extract .3dcpack and return the ``cExtensions/<ExtName>`` folder."""
    with zipfile.ZipFile(pack_path, "r") as zf:
        zf.extractall(extract_dir)
    addon_root = (
        extract_dir / "UserPrefs" / "Scripts" / "cExtensions" / ext_name
    )
    if not addon_root.is_dir():
        raise FileNotFoundError(
            f"Extracted pack missing addon root: {addon_root}"
        )
    entry = addon_root / f"{ext_name}.py"
    if not entry.is_file():
        raise FileNotFoundError(
            f"Extracted pack missing entry script: {entry}"
        )
    return addon_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Vendor slim lks_utils, probe isolated imports, build a side-install "
            ".3dcpack (never named LKS)."
        )
    )
    parser.add_argument(
        "--ext-name",
        type=str,
        default=_DEFAULT_EXT,
        help=f"Side-install folder/entry name (default: {_DEFAULT_EXT})",
    )
    parser.add_argument(
        "--install-local",
        action="store_true",
        help="Also copy into cExtensions/<ext-name>/ for live testing",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing --install-local destination",
    )
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="Optional version string for the artifact name",
    )
    parser.add_argument(
        "--skip-extract-probe",
        action="store_true",
        help="Skip re-probe of the extracted .3dcpack (not recommended)",
    )
    args = parser.parse_args(argv)

    try:
        ext_name = _validate_side_ext_name(args.ext_name)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    vendor = _load_vendor()
    probe = _load_probe()
    did_vendor = False
    exit_code = 1

    print()
    print("=" * 60)
    print(" LKS side-install package + isolated import probe")
    print("=" * 60)
    print(f"  ExtName:  {ext_name}")
    print(f"  Install:  {'yes' if args.install_local else 'pack only'}")
    print(f"  Live LKS: protected (refused as --ext-name)")
    print()

    try:
        # --- 1) Vendor slim real files ---------------------------------
        print("[1/4] Vendoring slim lks_utils (no junction)...")
        vendor.cmd_vendor()
        did_vendor = True
        bundle = _LKS_ROOT / "lks_utils"
        if vendor.is_junction(bundle):
            raise RuntimeError("lks_utils/ is still a junction after --vendor")
        probe.assert_no_junctions(bundle)
        size = probe.assert_bundle_size_ok(bundle)
        print(f"  Slim bundle: {size / 1024:.1f} KB (junction-free)")
        print()

        # --- 2) Isolated import probe (pre-pack) -----------------------
        print("[2/4] Pure-Python import probe (sandbox, no external path)...")
        sandbox = probe.build_default_sandbox_from_vendor()
        probe.probe_addon_root(sandbox)
        print()

        # --- 3) Build .3dcpack -----------------------------------------
        print("[3/4] Packaging .3dcpack...")
        pack_path = _run_pack_subprocess(
            ext_name,
            install_local=args.install_local,
            force=args.force,
            version=args.version,
        )
        print(f"  Pack: {pack_path}")
        print()

        # --- 4) Re-probe the exact shipped archive ---------------------
        if not args.skip_extract_probe:
            print("[4/4] Re-probing extracted .3dcpack contents...")
            with tempfile.TemporaryDirectory(prefix="lks_pack_probe_") as tmp:
                extract_dir = Path(tmp)
                addon_root = _extract_pack_addon_root(
                    pack_path, extract_dir, ext_name
                )
                probe.assert_no_junctions(addon_root / "lks_utils")
                probe.probe_addon_root(addon_root)
            print()
        else:
            print("[4/4] Skipping extracted-pack probe (--skip-extract-probe)")
            print()

        print("=" * 60)
        print(" PASS - isolated imports OK; side-install pack ready")
        print("=" * 60)
        print(f"  ExtName:   {ext_name}")
        print(f"  Artifact:  {pack_path}")
        print(f"  Install:   Drag .3dcpack into 3DCoat (or use --install-local)")
        print(f"  Enable:    Extensions / Start / {ext_name}")
        print(f"  Note:      Live folder 'LKS' was not modified")
        print()
        exit_code = 0
    except Exception as exc:
        print()
        print(f"FAIL: {exc}")
        exit_code = 1
    finally:
        if did_vendor:
            print("Restoring lks_utils/ junction for local development...")
            try:
                vendor.cmd_link()
            except Exception as restore_exc:  # noqa: BLE001
                print(f"[!] Junction restore failed: {restore_exc}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
