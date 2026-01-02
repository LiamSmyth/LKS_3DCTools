"""
Toggle 16x decimation proxy for selected object.

Room: Sculpt
Action: Toggle 16x decimation cache (proxy mode)
"""
from _utils.mesh_utils import CMD_DECIMATE_16X
from _utils.coat_ui_utils import show_message
import coat


def main() -> None:
    """Toggle 16x decimation proxy."""
    coat.ui.cmd(CMD_DECIMATE_16X)
    coat.ui.cmd("$ToggleCachingVolume")
    show_message("16x decimation proxy toggled", 3000)


main()
