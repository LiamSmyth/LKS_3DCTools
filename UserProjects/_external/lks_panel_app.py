#!/usr/bin/env python
"""
LKS Panel Application Entry Point.

This is the main entry point for the external panel. It handles:
1. Self-healing dependency installation
2. Launching the panel application

Run this script directly or via 3DCoat's coat.io.exec().
"""
from __future__ import annotations

import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import List

# =============================================================================
# LOGGING (for debugging subprocess issues)
# =============================================================================

# Log file location - same folder as this script
LOG_FILE: Path = Path(__file__).parent / "lks_panel_log.txt"


def log(message: str) -> None:
    """Write a message to the log file."""
    timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass  # Can't log, oh well


def log_exception(context: str) -> None:
    """Log the current exception with full traceback."""
    log(f"EXCEPTION in {context}:")
    log(traceback.format_exc())


# =============================================================================
# CONFIGURATION
# =============================================================================

# Required packages for the panel
REQUIRED_PACKAGES: List[str] = [
    "dearpygui",  # Modern GPU-accelerated GUI framework
]

# Optional packages (nice to have, but not required)
OPTIONAL_PACKAGES: List[str] = []


# =============================================================================
# DEPENDENCY CHECKING
# =============================================================================

def is_installed(package: str) -> bool:
    """Check if a Python package is installed."""
    # Handle package names with hyphens (e.g., 'scikit-image' -> 'scikit_image')
    module_name: str = package.replace("-", "_")
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def get_missing_packages(packages: List[str]) -> List[str]:
    """Get list of packages that are not installed."""
    return [pkg for pkg in packages if not is_installed(pkg)]


def install_packages(packages: List[str]) -> bool:
    """Install packages using pip. Returns True if successful."""
    if not packages:
        return True

    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", *packages
        ])
        return True
    except subprocess.CalledProcessError:
        return False


# =============================================================================
# SELF-HEALING BOOTSTRAP
# =============================================================================

def check_and_install_dependencies() -> bool:
    """Check for missing dependencies and offer to install them.

    Since we can't use tkinter (not in bundled Python), we use a simple
    console-based prompt or just auto-install.

    Returns True if all dependencies are available (or were installed).
    Returns False if installation failed.
    """
    missing: List[str] = get_missing_packages(REQUIRED_PACKAGES)

    if not missing:
        log("All dependencies already installed")
        return True

    # Auto-install missing packages (no GUI available yet)
    log(f"Installing required packages: {', '.join(missing)}")
    print(f"Installing required packages: {', '.join(missing)}")
    print("Please wait...")

    success: bool = install_packages(missing)

    if success:
        log("Installation complete!")
        print("Installation complete!")
        return True
    else:
        log(f"ERROR: Failed to install packages: {', '.join(missing)}")
        print(f"ERROR: Failed to install packages: {', '.join(missing)}")
        print(f"Try installing manually: pip install {' '.join(missing)}")
        return False


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    """Main entry point."""
    log("=" * 60)
    log("LKS Panel starting...")
    log(f"Python: {sys.executable}")
    log(f"Version: {sys.version}")
    log(f"Script: {__file__}")

    try:
        # Check and install dependencies
        if not check_and_install_dependencies():
            log("Dependency check failed, exiting")
            sys.exit(1)

        # Now we can import and run the panel
        # Need to add our directory to the path
        script_dir: Path = Path(__file__).parent
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))

        # Also add UserProjects for importing _utils
        userprojects_dir: Path = script_dir.parent
        if str(userprojects_dir) not in sys.path:
            sys.path.insert(0, str(userprojects_dir))

        log(f"sys.path updated, importing lks_panel.app...")
        log(f"  script_dir: {script_dir}")
        log(f"  userprojects_dir: {userprojects_dir}")

        # Import and run
        from lks_panel.app import main as run_app
        log("Import successful, running app...")
        run_app()
        log("App exited normally")

    except Exception:
        log_exception("main()")
        raise  # Re-raise so it's visible if running interactively


if __name__ == "__main__":
    main()
