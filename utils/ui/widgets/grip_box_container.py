"""GripBoxContainer — re-exported from lks_utils QGripBoxContainer.

Uses ``item_id`` instead of the old ``state_key`` parameter name.
Has ``order_changed`` signal for persistence.
"""
from __future__ import annotations
from lks_utils.gui_qt.widgets.grip_box_container import QGripBoxContainer as GripBoxContainer

__all__ = ["GripBoxContainer"]
