#!/usr/bin/env python3
"""
Package LKS cModule for distribution.

Creates distributable archives with proper 3DCoat installation structure:
- Standard .zip: LKS/<files>
- Installable .3dcpack: UserPrefs/Scripts/cExtensions/LKS/<files>

Exclusion patterns are read from:
- .gitignore (standard git exclusions)
- .gitignore-remote (files excluded from remote push)
- .gitignore-package (package-specific exclusions)

Usage:
    python package_release.py
    python package_release.py --version 1.0.0
    python package_release.py --output C:/path/to/output
    python package_release.py --dry-run  # Preview files
    python package_release.py --pack-only  # Only create .3dcpack
"""
from __future__ import annotations

import argparse
import fnmatch
import shutil
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
    files: list[Path] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        # Check if path matches any exclusion pattern
        if matches_pattern(path, root, patterns):
            continue

        files.append(path)

    return files


# =============================================================================
# PACKAGE CREATION
# =============================================================================

def create_standard_zip(
    source_dir: Path,
    output_dir: Path,
    version: str | None = None,
    files: list[Path] | None = None,
) -> Path:
    """Create a standard .zip with LKS/<files> structure.

    Args:
        source_dir: Root directory of the LKS cModule
        output_dir: Directory to write the zip file to
        version: Optional version string (e.g., "1.0.0")
        files: Optional pre-collected files to include

    Returns:
        Path to the created zip file
    """
    # Build output filename
    timestamp = datetime.now().strftime("%Y%m%d")
    if version:
        zip_name = f"LKS_3DCoat_cModule_v{version}.zip"
    else:
        zip_name = f"LKS_3DCoat_cModule_{timestamp}.zip"

    output_path = output_dir / zip_name

    # Collect files if not provided
    if files is None:
        patterns = load_exclusion_patterns(source_dir)
        files = collect_files(source_dir, patterns)

    print(f"Creating standard .zip package...")
    print(f"  Output: {output_path}")
    print(f"  Files:  {len(files)}")

    # Create zip file with LKS/<files> structure
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(files):
            rel_path = file_path.relative_to(source_dir)
            arc_path = Path("LKS") / rel_path
            zf.write(file_path, arc_path)

    size_kb = output_path.stat().st_size / 1024
    print(f"  Created: {output_path.name} ({size_kb:.1f} KB)")

    return output_path


def create_3dcpack(
    source_dir: Path,
    output_dir: Path,
    version: str | None = None,
    files: list[Path] | None = None,
) -> Path:
    """Create an installable .3dcpack with proper directory structure.

    The .3dcpack format is a .zip file with:
    - Archive root: UserPrefs/Scripts/cExtensions/LKS/<files>
    - File extension: .3dcpack (renamed from .zip)

    This allows users to drag-and-drop install directly into 3DCoat.

    Args:
        source_dir: Root directory of the LKS cModule
        output_dir: Directory to write the .3dcpack file to
        version: Optional version string (e.g., "1.0.0")
        files: Optional pre-collected files to include

    Returns:
        Path to the created .3dcpack file
    """
    # Build output filename
    timestamp = datetime.now().strftime("%Y%m%d")
    if version:
        pack_name = f"LKS_3DCoat_cModule_v{version}.3dcpack"
    else:
        pack_name = f"LKS_3DCoat_cModule_{timestamp}.3dcpack"

    output_path = output_dir / pack_name

    # Collect files if not provided
    if files is None:
        patterns = load_exclusion_patterns(source_dir)
        files = collect_files(source_dir, patterns)

    print(f"Creating installable .3dcpack...")
    print(f"  Output: {output_path}")
    print(f"  Files:  {len(files)}")

    # Create zip file with UserPrefs/Scripts/cExtensions/LKS/<files> structure
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(files):
            rel_path = file_path.relative_to(source_dir)
            # 3DCoat installation path structure
            arc_path = Path("UserPrefs") / "Scripts" / \
                "cExtensions" / "LKS" / rel_path
            zf.write(file_path, arc_path)

    size_kb = output_path.stat().st_size / 1024
    print(f"  Created: {output_path.name} ({size_kb:.1f} KB)")

    return output_path


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Package LKS cModule for distribution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
        help="Output directory (default: parent of source directory)"
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

    args = parser.parse_args()

    # Determine paths
    source_dir = Path(__file__).parent.resolve()
    output_dir = Path(args.output).resolve(
    ) if args.output else source_dir.parent

    # Load exclusion patterns
    print("Loading exclusion patterns...")
    patterns = load_exclusion_patterns(source_dir)
    print(f"  Loaded {len(patterns)} patterns from:")
    for filename in EXCLUSION_FILES:
        if (source_dir / filename).exists():
            print(f"    - {filename}")
    print()

    # Collect files
    print("Collecting files...")
    files = collect_files(source_dir, patterns)
    print(f"  Found {len(files)} files to include")
    print()

    # Dry run mode
    if args.dry_run:
        print("Files that would be included in package:")
        print()
        for f in sorted(files):
            rel_path = f.relative_to(source_dir)
            print(f"  {rel_path}")
        print()
        print(f"Total: {len(files)} files")
        return

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create packages
    print(f"Source: {source_dir}")
    print(f"Output: {output_dir}")
    print()

    created_files: list[Path] = []

    # Create standard .zip (unless --pack-only)
    if not args.pack_only:
        zip_path = create_standard_zip(
            source_dir, output_dir, args.version, files)
        created_files.append(zip_path)
        print()

    # Create installable .3dcpack
    pack_path = create_3dcpack(source_dir, output_dir, args.version, files)
    created_files.append(pack_path)
    print()

    # Summary
    print("=" * 60)
    print("Package creation complete!")
    print()
    for path in created_files:
        size_kb = path.stat().st_size / 1024
        print(f"  {path.name}")
        print(f"    {size_kb:.1f} KB")
    print()
    print("Installation instructions:")
    print("  - For .zip: Extract and manually copy to cExtensions folder")
    print("  - For .3dcpack: Drag and drop into 3DCoat window to install")


if __name__ == "__main__":
    main()
