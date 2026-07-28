#!/usr/bin/env python3
"""
Package LKS cModule for distribution.

Creates distributable archives with proper 3DCoat installation structure:
- Standard .zip: <ExtName>/<files>
- Installable .3dcpack: UserPrefs/Scripts/cExtensions/<ExtName>/<files>

Exclusion patterns are read from:
- .gitignore (standard git exclusions)
- .gitignore-remote (files excluded from remote push)
- .gitignore-package (package-specific exclusions)

Usage:
    python package_release.py
    python package_release.py --version 1.0.0
    python package_release.py --ext-name LKS_Side --install-local
    python package_release.py --ext-name LKS_Side --pack-only
    python package_release.py --dry-run
    python package_release.py --keep-vendored

Side-by-side testing:
    3DCoat Start loads ``cExtensions/<ExtName>/<ExtName>.py``. Use
    ``--ext-name`` so the pack installs beside your live ``LKS`` folder
    instead of overwriting it. ``--install-local`` copies straight into
    ``cExtensions/<ExtName>/`` (same parent as this repo).

Before archiving, runs tools/vendor_lks_utils.py to copy only the lks_utils
modules imported by LKS into ``lks_utils/`` (~0.5 MB). Restores the
dev junction afterward unless --keep-vendored. Runtime needs only the addon
root on sys.path — no external lks_utils path.
"""
from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import re
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path


# =============================================================================
# EXCLUSION PATTERN FILES
# =============================================================================

EXCLUSION_FILES: list[str] = [
    ".gitignore",
    ".gitignore-remote",
    ".gitignore-package",
]

# Ship the slim bundled lks_utils even though lks_utils/ is gitignored
# (dev uses a junction; release copies real files via --vendor).
FORCE_INCLUDE_PREFIXES: tuple[str, ...] = (
    "lks_utils/",
)

_DEFAULT_EXT_NAME: str = "LKS"
_EXT_NAME_RE: re.Pattern[str] = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# Source entry module that implements the cExtension + panel bootstrap
_SOURCE_ENTRY_PY: str = "LKS.py"


# =============================================================================
# PATTERN MATCHING
# =============================================================================

def load_exclusion_patterns(root: Path) -> list[str]:
    """Load exclusion patterns from all gitignore-style files.

    Args:
        root: Root directory of the cModule

    Returns:
        List of exclusion patterns (gitignore syntax)
    """
    patterns: list[str] = []

    for filename in EXCLUSION_FILES:
        file_path = root / filename
        if not file_path.exists():
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                patterns.append(line)

    return patterns


def normalize_pattern(pattern: str) -> str:
    """Normalize a gitignore pattern for matching.

    Args:
        pattern: Raw gitignore pattern

    Returns:
        Normalized pattern
    """
    # Remove leading ./
    if pattern.startswith("./"):
        pattern = pattern[2:]

    # Handle directory patterns (trailing /)
    if pattern.endswith("/"):
        pattern = pattern[:-1]

    return pattern


def matches_pattern(path: Path, root: Path, patterns: list[str]) -> bool:
    """Check if a path matches any exclusion pattern.

    Args:
        path: Path to check
        root: Root directory
        patterns: List of gitignore-style patterns

    Returns:
        True if path should be excluded
    """
    rel_path = path.relative_to(root)
    rel_path_str = str(rel_path).replace("\\", "/")
    parts = rel_path.parts

    # Force-include prefixes win over exclusion patterns (e.g. vendored deps)
    for prefix in FORCE_INCLUDE_PREFIXES:
        if rel_path_str == prefix.rstrip("/") or rel_path_str.startswith(prefix):
            return False

    for pattern in patterns:
        pattern = normalize_pattern(pattern)

        # Handle negation patterns (!)
        if pattern.startswith("!"):
            # Negation patterns not supported in this simple implementation
            continue

        # Handle ** (match zero or more directories)
        if "**" in pattern:
            # Convert ** to * for fnmatch (simplified)
            pattern = pattern.replace("**", "*")

        # Check if pattern matches the relative path
        if fnmatch.fnmatch(rel_path_str, pattern):
            return True

        # Check if pattern matches just the filename
        if fnmatch.fnmatch(path.name, pattern):
            return True

        # Check if pattern matches any parent directory
        for part in parts:
            if fnmatch.fnmatch(part, pattern):
                return True
            # Also check full pattern against directory path
            part_path = ""
            for p in parts:
                part_path = part_path + "/" + p if part_path else p
                if fnmatch.fnmatch(part_path, pattern):
                    return True
                if part_path == rel_path_str:
                    break

    return False


def _load_vendor_module(source_dir: Path):  # type: ignore[no-untyped-def]
    """Import tools/vendor_lks_utils.py by path."""
    vendor_script: Path = source_dir / "tools" / "vendor_lks_utils.py"
    if not vendor_script.is_file():
        return None
    spec = importlib.util.spec_from_file_location(
        "lks_vendor_lks_utils", vendor_script
    )
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["lks_vendor_lks_utils"] = mod
    spec.loader.exec_module(mod)
    return mod


def ensure_slim_vendor(source_dir: Path) -> bool:
    """Build slim <LKS>/lks_utils/ real files for packaging.

    Returns:
        True if bundling ran successfully.
    """
    mod = _load_vendor_module(source_dir)
    if mod is None:
        print("WARNING: tools/vendor_lks_utils.py not found — skipping vendor step")
        return False
    print("Bundling slim lks_utils into addon root...")
    mod.cmd_vendor()
    print()
    return True


def restore_vendor_link(source_dir: Path) -> None:
    """Re-create lks_utils/ junction for local development."""
    mod = _load_vendor_module(source_dir)
    if mod is None:
        return
    print("Restoring lks_utils/ junction for local development...")
    mod.cmd_link()
    print()


# =============================================================================
# FILE COLLECTION
# =============================================================================

def collect_files(root: Path, patterns: list[str]) -> list[Path]:
    """Collect all files that should be included in the package.

    Args:
        root: Root directory of the cModule
        patterns: Exclusion patterns

    Returns:
        List of Path objects to include
    """
    # Never walk a live junction — that would ship the entire lks_utils tree.
    bundle_lks: Path = root / "lks_utils"
    skip_junction_bundle: bool = False
    if bundle_lks.exists():
        mod = _load_vendor_module(root)
        if mod is not None and mod.is_junction(bundle_lks):
            skip_junction_bundle = True
            print(
                "  NOTE: lks_utils/ is a junction — excluded from package "
                "(run without --skip-vendor to ship a slim copy)"
            )

    files: list[Path] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if skip_junction_bundle:
            try:
                _ = path.relative_to(bundle_lks)
                continue
            except ValueError:
                pass

        if matches_pattern(path, root, patterns):
            continue

        files.append(path)

    return files


# =============================================================================
# EXTENSION NAME / ENTRY SCRIPT
# =============================================================================

def validate_ext_name(name: str) -> str:
    """Validate a cExtension folder / entry-module name."""
    if not _EXT_NAME_RE.match(name):
        raise ValueError(
            f"Invalid --ext-name {name!r}: use letters, digits, underscore; "
            "must start with a letter or underscore (valid Python identifier)."
        )
    return name


def entry_script_name(ext_name: str) -> str:
    """Return ``<ExtName>.py`` — what 3DCoat Start loads for the folder."""
    return f"{ext_name}.py"


def package_member_rel_paths(
    source_dir: Path,
    files: list[Path],
    ext_name: str,
) -> list[tuple[Path, Path]]:
    """Map archive-relative paths → source files for packing/install.

    Ensures ``<ext_name>.py`` exists in the package (copied from LKS.py when
    the extension is renamed for side-by-side installs).
    """
    members: list[tuple[Path, Path]] = []
    entry_name: str = entry_script_name(ext_name)
    has_matching_entry: bool = False

    for file_path in sorted(files):
        rel_path: Path = file_path.relative_to(source_dir)
        if rel_path.as_posix() == entry_name:
            has_matching_entry = True
        members.append((rel_path, file_path))

    if not has_matching_entry:
        source_entry: Path = source_dir / _SOURCE_ENTRY_PY
        if not source_entry.is_file():
            raise FileNotFoundError(
                f"Missing entry script {source_entry} (needed to build {entry_name})"
            )
        members.append((Path(entry_name), source_entry))
        print(f"  + entry script: {entry_name}  (from {_SOURCE_ENTRY_PY})")

    return members


def artifact_basename(ext_name: str, version: str | None) -> str:
    """Build zip/3dcpack basename without extension."""
    timestamp: str = datetime.now().strftime("%Y%m%d")
    if version:
        return f"{ext_name}_3DCoat_cModule_v{version}"
    if ext_name == _DEFAULT_EXT_NAME:
        return f"LKS_3DCoat_cModule_{timestamp}"
    return f"{ext_name}_3DCoat_cModule_{timestamp}"


# =============================================================================
# PACKAGE CREATION
# =============================================================================

def create_standard_zip(
    source_dir: Path,
    output_dir: Path,
    version: str | None = None,
    files: list[Path] | None = None,
    ext_name: str = _DEFAULT_EXT_NAME,
) -> Path:
    """Create a standard .zip with ``<ExtName>/<files>`` structure."""
    if files is None:
        patterns = load_exclusion_patterns(source_dir)
        files = collect_files(source_dir, patterns)

    members = package_member_rel_paths(source_dir, files, ext_name)
    output_path = output_dir / f"{artifact_basename(ext_name, version)}.zip"

    print("Creating standard .zip package...")
    print(f"  ExtName: {ext_name}")
    print(f"  Output:  {output_path}")
    print(f"  Files:   {len(members)}")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_path, file_path in members:
            arc_path = Path(ext_name) / rel_path
            zf.write(file_path, arc_path)

    size_kb = output_path.stat().st_size / 1024
    print(f"  Created: {output_path.name} ({size_kb:.1f} KB)")
    return output_path


def create_3dcpack(
    source_dir: Path,
    output_dir: Path,
    version: str | None = None,
    files: list[Path] | None = None,
    ext_name: str = _DEFAULT_EXT_NAME,
) -> Path:
    """Create an installable .3dcpack under ``cExtensions/<ExtName>/``."""
    if files is None:
        patterns = load_exclusion_patterns(source_dir)
        files = collect_files(source_dir, patterns)

    members = package_member_rel_paths(source_dir, files, ext_name)
    output_path = output_dir / f"{artifact_basename(ext_name, version)}.3dcpack"

    print("Creating installable .3dcpack...")
    print(f"  ExtName: {ext_name}")
    print(f"  Output:  {output_path}")
    print(f"  Files:   {len(members)}")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_path, file_path in members:
            arc_path = (
                Path("UserPrefs") / "Scripts" / "cExtensions" / ext_name / rel_path
            )
            zf.write(file_path, arc_path)

    size_kb = output_path.stat().st_size / 1024
    print(f"  Created: {output_path.name} ({size_kb:.1f} KB)")
    return output_path


def install_local(
    source_dir: Path,
    files: list[Path],
    ext_name: str,
    dest_dir: Path | None = None,
    force: bool = False,
) -> Path:
    """Copy a side-install tree into ``cExtensions/<ExtName>/``.

    Args:
        source_dir: Live LKS repo root
        files: Collected package files (must include real lks_utils/)
        ext_name: Destination folder / entry-script name
        dest_dir: Override destination (default: sibling of source_dir)
        force: Overwrite an existing destination folder

    Returns:
        Path to the installed extension root
    """
    if dest_dir is None:
        dest_dir = source_dir.parent / ext_name
    dest_dir = dest_dir.resolve()

    if dest_dir == source_dir.resolve():
        raise ValueError(
            "Refusing to install over the source LKS tree. "
            "Choose a different --ext-name."
        )

    if dest_dir.exists():
        if not force:
            raise FileExistsError(
                f"Destination already exists: {dest_dir}\n"
                "Pass --force to overwrite, or pick another --ext-name."
            )
        print(f"  Removing existing: {dest_dir}")
        shutil.rmtree(dest_dir)

    members = package_member_rel_paths(source_dir, files, ext_name)
    print(f"Installing local side extension...")
    print(f"  ExtName: {ext_name}")
    print(f"  Dest:    {dest_dir}")
    print(f"  Files:   {len(members)}")

    for rel_path, file_path in members:
        out_path: Path = dest_dir / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, out_path)

    entry: Path = dest_dir / entry_script_name(ext_name)
    if not entry.is_file():
        raise RuntimeError(f"Entry script missing after install: {entry}")

    print(f"  Entry:   {entry.name}  (3DCoat Start loads this)")
    print(f"  Done:    enable '{ext_name}' in 3DCoat Extensions")
    return dest_dir


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Package LKS cModule for distribution / side-by-side test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Side-by-side example:\n"
            "  python package_release.py --ext-name LKS_Side --install-local --force\n"
            "  python package_release.py --ext-name LKS_Side --pack-only\n"
        ),
    )
    parser.add_argument(
        "--version", "-v",
        type=str,
        default=None,
        help="Version string (e.g., 1.0.0)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output directory for zip/3dcpack (default: parent of source)"
    )
    parser.add_argument(
        "--ext-name",
        type=str,
        default=_DEFAULT_EXT_NAME,
        help=(
            "cExtension folder + entry script name (default: LKS). "
            "Use e.g. LKS_Side so 3DCoat installs beside live LKS."
        ),
    )
    parser.add_argument(
        "--install-local",
        action="store_true",
        help=(
            "Copy the packaged tree to cExtensions/<ext-name>/ "
            "(sibling of this repo) for side-by-side testing"
        ),
    )
    parser.add_argument(
        "--install-dir",
        type=str,
        default=None,
        help="Override --install-local destination directory",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing --install-local destination",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be included without creating archives"
    )
    parser.add_argument(
        "--pack-only",
        action="store_true",
        help="Only create .3dcpack (skip standard .zip)"
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Skip zip/3dcpack (useful with --install-local only)",
    )
    parser.add_argument(
        "--skip-vendor",
        action="store_true",
        help="Skip slim lks_utils bundling (use existing lks_utils/ as-is)"
    )
    parser.add_argument(
        "--keep-vendored",
        action="store_true",
        help="Leave real bundled lks_utils/ files (do not restore junction)"
    )

    args = parser.parse_args()
    try:
        ext_name: str = validate_ext_name(args.ext_name)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(2) from exc

    source_dir = Path(__file__).parent.resolve()
    output_dir = Path(args.output).resolve(
    ) if args.output else source_dir.parent

    did_vendor: bool = False
    if not args.skip_vendor:
        did_vendor = ensure_slim_vendor(source_dir)

    print("Loading exclusion patterns...")
    patterns = load_exclusion_patterns(source_dir)
    print(f"  Loaded {len(patterns)} patterns from:")
    for filename in EXCLUSION_FILES:
        if (source_dir / filename).exists():
            print(f"    - {filename}")
    print()

    print("Collecting files...")
    files = collect_files(source_dir, patterns)
    vendor_files = [
        f for f in files
        if str(f.relative_to(source_dir)).replace("\\", "/").startswith("lks_utils/")
    ]
    print(f"  Found {len(files)} files to include ({len(vendor_files)} under lks_utils/)")
    if ext_name != _DEFAULT_EXT_NAME:
        print(f"  ExtName: {ext_name}  -> entry {entry_script_name(ext_name)}")
    print()

    if args.dry_run:
        print("Files that would be included in package:")
        print()
        for rel_path, _src in package_member_rel_paths(source_dir, files, ext_name):
            print(f"  {rel_path}")
        print()
        print(f"Total: {len(files)} source files (+ entry script if renamed)")
        if did_vendor and not args.keep_vendored:
            restore_vendor_link(source_dir)
        return

    created_files: list[Path] = []
    install_path: Path | None = None

    if args.install_local:
        dest = Path(args.install_dir).resolve() if args.install_dir else None
        try:
            install_path = install_local(
                source_dir,
                files,
                ext_name,
                dest_dir=dest,
                force=args.force,
            )
        except (FileExistsError, ValueError) as exc:
            print(f"ERROR: {exc}")
            if did_vendor and not args.keep_vendored:
                restore_vendor_link(source_dir)
            raise SystemExit(1) from exc
        print()

    if not args.no_archive:
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Source: {source_dir}")
        print(f"Output: {output_dir}")
        print()

        if not args.pack_only:
            zip_path = create_standard_zip(
                source_dir, output_dir, args.version, files, ext_name=ext_name
            )
            created_files.append(zip_path)
            print()

        pack_path = create_3dcpack(
            source_dir, output_dir, args.version, files, ext_name=ext_name
        )
        created_files.append(pack_path)
        print()

    if did_vendor and not args.keep_vendored:
        restore_vendor_link(source_dir)

    print("=" * 60)
    print("Package creation complete!")
    print()
    if install_path is not None:
        print(f"  Local install: {install_path}")
        print(f"    Enable extension '{ext_name}' in 3DCoat (Start).")
        print()
    for path in created_files:
        size_kb = path.stat().st_size / 1024
        print(f"  {path.name}")
        print(f"    {size_kb:.1f} KB")
    if created_files:
        print()
        print("Installation instructions:")
        print("  - For .zip: Extract and copy the folder into cExtensions/")
        print("  - For .3dcpack: Drag and drop into 3DCoat window to install")
        if ext_name != _DEFAULT_EXT_NAME:
            print(
                f"  - Side test: installs as cExtensions/{ext_name}/ "
                f"(does not overwrite LKS/)"
            )


if __name__ == "__main__":
    main()