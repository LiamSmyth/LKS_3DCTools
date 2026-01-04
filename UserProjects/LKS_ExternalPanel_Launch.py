"""
Launch LKS External Panel.

Room: Any
Action: Launch the external panel window and register the IPC extension.

This script:
1. Registers the LKS extension (if not already registered)
2. Launches the external panel app as a separate process
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import coat


def find_python_executable() -> Optional[str]:
    """
    Find the Python executable for 3DCoat's embedded Python.

    In 3DCoat, sys.executable returns the 3DCoat app, not Python.
    We need to derive the Python path from coat.io.pythonPath().
    """
    # coat.io.pythonPath() returns the Python installation folder directly
    # e.g., C:/Users/.../Documents/3DCoat/python-3.11.9
    # python.exe is directly in that folder
    python_root: str = coat.io.pythonPath()
    root_path: Path = Path(python_root)

    # Check directly in the pythonPath folder (this is the actual location)
    candidates: list[Path] = [
        root_path / "python.exe",
        root_path / "pythonw.exe",  # Windowed version (no console)
        root_path / "python3.exe",
    ]

    # Also check legacy locations in case pythonPath returns site-packages
    candidates.extend([
        root_path.parent.parent / "python.exe",
        root_path.parent.parent / "pythonw.exe",
    ])

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


def main() -> None:
    """Launch the LKS external panel."""
    # Get paths
    userprojects_dir: Path = Path(__file__).parent
    external_app: Path = userprojects_dir / "_external" / "lks_panel_app.py"

    if not external_app.exists():
        coat.ui.showInfoMessage(
            f"Error: Panel app not found at {external_app}", 5000
        )
        return

    # Add UserProjects to path for imports
    if str(userprojects_dir) not in sys.path:
        sys.path.insert(0, str(userprojects_dir))

    # Register the extension
    try:
        from _utils.lks_extension import register_extension, is_extension_registered

        if not is_extension_registered():
            register_extension()
            coat.ui.showInfoMessage("LKS Extension: Registered", 2000)
    except Exception as e:
        coat.ui.showInfoMessage(f"Extension error: {e}", 3000)
        return

    # Find the Python executable
    python_exe: Optional[str] = find_python_executable()

    if python_exe is None:
        # Show debug info
        site_packages: str = coat.io.pythonPath()
        coat.ui.showInfoMessage(
            f"Error: Python executable not found. Site-packages: {site_packages}", 5000
        )
        return

    script_path: str = str(external_app)

    try:
        # coat.io.exec() launches non-blocking
        coat.io.exec(python_exe, script_path)
        coat.ui.showInfoMessage(
            f"LKS Panel: Launching with {Path(python_exe).name}...", 2000)
    except Exception as e:
        coat.ui.showInfoMessage(f"Launch error: {e}", 3000)


main()
