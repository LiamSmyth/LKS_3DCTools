"""
Radial menu - Main module with exports and tests.

A direction-based menu that appears at cursor position. Users move mouse
in a direction to select an action, then release trigger key to invoke.

Usage:
    from utils.ui.widgets.radial_menu import RadialMenuItem, RadialMenuWidget
    
    items = [
        RadialMenuItem(label="Action 1", action=do_action1, icon="🔻"),
        RadialMenuItem(label="Action 2", action=do_action2, icon="🔄"),
    ]
    
    menu = RadialMenuWidget()
    menu.set_items(items)
    menu.show_at(QCursor.pos())
"""

from __future__ import annotations

# When run as __main__, use absolute imports
if __name__ == "__main__":
    import sys
    from pathlib import Path
    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

    from utils.ui.widgets.radial_menu_model import RadialMenuItem
    from utils.ui.widgets.radial_menu_widget import RadialMenuWidget
    HAS_QT = True
else:
    # Normal relative imports when imported as module
    from .radial_menu_model import RadialMenuItem
    try:
        from .radial_menu_widget import RadialMenuWidget
        HAS_QT = True
    except ImportError:
        HAS_QT = False
        RadialMenuWidget = None

__all__ = ["RadialMenuItem", "RadialMenuWidget"]

# =============================================================================
# STANDALONE TESTS
# =============================================================================


def test_geometry():
    """Test geometry calculations."""
    if __name__ == "__main__":
        from utils.ui.widgets.radial_menu_geometry import (
            cursor_to_angle,
            distribute_node_angles,
            calculate_slice_boundaries,
            angle_in_slice,
        )
    else:
        from .radial_menu_geometry import (
            cursor_to_angle,
            distribute_node_angles,
            calculate_slice_boundaries,
            angle_in_slice,
        )

    print("\\n" + "="*60)
    print("GEOMETRY TEST - Phase 1.2")
    print("="*60)

    # Test cursor_to_angle
    if HAS_QT:
        from PySide6.QtCore import QPoint

        anchor = QPoint(100, 100)

        test_cases = [
            (QPoint(100, 50), "Up", 0.0),
            (QPoint(150, 100), "Right", 90.0),
            (QPoint(100, 150), "Down", 180.0),
            (QPoint(50, 100), "Left", 270.0),
        ]

        print("\\ncursor_to_angle tests:")
        for cursor, label, expected in test_cases:
            angle = cursor_to_angle(cursor, anchor)
            status = "OK" if abs(angle - expected) < 1.0 else "FAIL"
            print(
                f"  {status} {label:6s}: {angle:6.1f} deg (expected {expected:6.1f} deg)")

    # Test distribute_node_angles
    items = [
        RadialMenuItem(label=f"Item {i}", action=lambda: None)
        for i in range(4)
    ]
    angles = distribute_node_angles(items)
    print(f"\\nDistribute 4 nodes evenly:")
    for i, angle in enumerate(angles):
        print(f"  Node {i}: {angle:6.1f} deg")

    # Test slice boundaries
    leaf_angles = [0.0, 90.0, 180.0, 270.0]
    boundaries = calculate_slice_boundaries(leaf_angles)
    print(f"\\nSlice boundaries for {leaf_angles}:")
    for i, (lower, upper) in enumerate(boundaries):
        print(f"  Slice {i}: {lower:6.1f} to {upper:6.1f} deg")

    # Test angle_in_slice
    print(f"\\nangle_in_slice tests:")
    test_angles = [45.0, 135.0, 315.0]
    for test_angle in test_angles:
        for i, (lower, upper) in enumerate(boundaries):
            if angle_in_slice(test_angle, lower, upper):
                print(f"  {test_angle} deg is in slice {i}")
                break

    print("="*60 + "\\n")


def test_standalone():
    """
    Test the radial menu in standalone mode.

    Run with: python radial_menu.py
    Or from 3DCoat's Python: python.exe radial_menu.py
    """
    if not HAS_QT:
        print("ERROR: PySide6 not available")
        return

    import sys
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QPoint

    # First test geometry
    test_geometry()

    # Create application
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    # Create test menu items
    def action_1():
        print(">>> Decimate 50% invoked")
        app.quit()

    def action_2():
        print(">>> Resample Half invoked")
        app.quit()

    def action_3():
        print(">>> Ghost Toggle invoked")
        app.quit()

    def action_4():
        print(">>> To Surface invoked")
        app.quit()

    items = [
        RadialMenuItem(label="Decimate 50%", action=action_1, icon="🔻"),
        RadialMenuItem(label="Resample Half", action=action_2, icon="🔄"),
        RadialMenuItem(label="Ghost Toggle", action=action_3, icon="👻"),
        RadialMenuItem(label="To Surface", action=action_4, icon="⚙️"),
    ]

    # Create and show widget
    menu = RadialMenuWidget()
    menu.set_items(items)

    # Show at screen center
    screen = app.primaryScreen().geometry()
    center = QPoint(screen.width() // 2, screen.height() // 2)
    menu.show_at(center)

    print("\\n" + "="*60)
    print("RADIAL MENU TEST - Phase 1.3 (Painting)")
    print("="*60)
    print("The menu should appear at screen center with:")
    print("  • Dead zone circle in center")
    print("  • Four sectors with icons and labels")
    print("  • Dotted separator lines")
    print("\\nMove mouse to highlight sectors.")
    print("The highlighted slice should match cursor direction.")
    print("Press any key while highlighting to invoke action.")
    print("Press Escape to close without invoking.")
    print("="*60 + "\\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    test_standalone()
