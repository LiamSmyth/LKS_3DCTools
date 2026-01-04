"""
Stop LKS External Panel.

Room: Any
Action: Stop the external panel and unregister the IPC extension.

This script:
1. Requests shutdown via IPC (panel will close gracefully)
2. Unregisters the extension
"""
from __future__ import annotations

import sys
from pathlib import Path

import coat


def main() -> None:
    """Stop the LKS external panel."""
    # Add UserProjects to path for imports
    userprojects_dir: Path = Path(__file__).parent
    if str(userprojects_dir) not in sys.path:
        sys.path.insert(0, str(userprojects_dir))

    try:
        from _utils.lks_extension import unregister_extension, is_extension_registered
        from _utils.ipc_protocol import request_shutdown

        if is_extension_registered():
            # Request shutdown - this will signal both extension and panel
            request_shutdown()

            # Give the extension time to process
            coat.io.step(10)

            # Unregister
            unregister_extension()
            coat.ui.showInfoMessage("LKS Panel: Stopped", 2000)
        else:
            # Just request shutdown in case panel is running without extension
            request_shutdown()
            coat.ui.showInfoMessage("LKS Panel: Stop signal sent", 2000)

    except Exception as e:
        coat.ui.showInfoMessage(f"Stop error: {e}", 3000)


main()
