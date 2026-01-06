#!/usr/bin/env python3
"""
Package LKS cModule for distribution.

Creates a clean zip file excluding development-only content:
- .git/, .github/, .vscode/, .docs/, .example_code/, _tools/
- __pycache__/, *.pyc, *.pyo
- .env, .gitignore, *.code-workspace
- data/*.log (debug logs)

Usage:
    python package_release.py
    python package_release.py --version 1.0.0
    python package_release.py --output C:/path/to/output
"""
from __future__ import annotations

import argparse
import shutil
import zipfile
from datetime import datetime
from pathlib import Path


# Directories to exclude entirely
EXCLUDE_DIRS: set[str] = {
    ".git",
    ".github",
    ".vscode",
    ".docs",
    ".example_code",
    "_tools",
    "__pycache__",
}

# File patterns to exclude
EXCLUDE_FILE_PATTERNS: set[str] = {
    ".env",
    ".gitignore",
    ".code-workspace",
    ".pyc",
    ".pyo",
    ".pyz",
}

# Specific files to exclude by name
EXCLUDE_FILES: set[str] = {
    "package_release.py",  # This script itself
}

# Patterns for files in data/ to exclude (e.g., debug logs)
EXCLUDE_DATA_PATTERNS: set[str] = {
    ".log",
}


def should_exclude_path(path: Path, root: Path) -> bool:
    """Check if a path should be excluded from the package."""
    rel_path = path.relative_to(root)
    parts = rel_path.parts

    # Check if any parent directory is in exclude list
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True

    # Check file-specific exclusions
    if path.is_file():
        name = path.name

        # Exact file name match
        if name in EXCLUDE_FILES:
            return True

        # Pattern match (suffix/extension)
        for pattern in EXCLUDE_FILE_PATTERNS:
            if name.endswith(pattern):
                return True

        # Special handling for data/ folder - exclude logs
        if len(parts) >= 2 and parts[0] == "data":
            for pattern in EXCLUDE_DATA_PATTERNS:
                if name.endswith(pattern):
                    return True

    return False


def collect_files(root: Path) -> list[Path]:
    """Collect all files that should be included in the package."""
    files: list[Path] = []

    for path in root.rglob("*"):
        if path.is_file() and not should_exclude_path(path, root):
            files.append(path)

    return files


def create_package(
    source_dir: Path,
    output_dir: Path,
    version: str | None = None,
) -> Path:
    """Create a zip package of the LKS cModule.

    Args:
        source_dir: Root directory of the LKS cModule
        output_dir: Directory to write the zip file to
        version: Optional version string (e.g., "1.0.0")

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

    # Collect files to include
    files = collect_files(source_dir)

    print(f"Packaging LKS cModule...")
    print(f"  Source: {source_dir}")
    print(f"  Output: {output_path}")
    print(f"  Files:  {len(files)}")
    print()

    # Create zip file
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(files):
            # Archive path: LKS/<relative_path>
            rel_path = file_path.relative_to(source_dir)
            arc_path = Path("LKS") / rel_path

            zf.write(file_path, arc_path)
            print(f"  + {rel_path}")

    print()
    print(f"Created: {output_path}")
    print(f"Size: {output_path.stat().st_size / 1024:.1f} KB")

    return output_path


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Package LKS cModule for distribution"
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
        help="Output directory (default: same as source)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be included without creating zip"
    )

    args = parser.parse_args()

    # Determine paths
    source_dir = Path(__file__).parent.resolve()
    output_dir = Path(args.output) if args.output else source_dir.parent

    if args.dry_run:
        print("Dry run - files that would be included:")
        print()
        files = collect_files(source_dir)
        for f in sorted(files):
            print(f"  {f.relative_to(source_dir)}")
        print()
        print(f"Total: {len(files)} files")
        return

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create package
    create_package(source_dir, output_dir, args.version)


if __name__ == "__main__":
    main()
