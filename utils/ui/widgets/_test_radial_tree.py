"""
Test Phase 2: Tree menu with nested submenus.

Tests:
- Branch node hover detection
- Dwell timer (250ms to enter submenu)
- Submenu navigation (push/pop menu stack)
- Exit node rendering
- Multi-level navigation

Usage:
    python _test_radial_tree.py
"""

from radial_menu import (
    RadialMenuItem,
    RadialMenuWidget,
    HAS_QT,
)
import sys
from pathlib import Path

# Add widgets directory to path to import radial_menu directly
sys.path.insert(0, str(Path(__file__).parent))

# Import directly - avoids coat dependency from utils/__init__.py

if HAS_QT:
    from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
    from PySide6.QtCore import Qt


def test_tree_menu():
    """Test tree menu with 2-3 levels of nesting."""
    if not HAS_QT:
        print("ERROR: PySide6 not available")
        return 1

    print("=== Testing Phase 2: Tree Menu ===")
    print("Instructions:")
    print("1. Click 'Show Tree Menu' button")
    print("2. Hover over 'Mesh Ops' (branch) for 250ms")
    print("3. Should enter submenu automatically")
    print("4. Hover over 'Exit' node to return to parent")
    print("5. Test 'Advanced' -> 'Filters' (3 levels)")
    print()

    app = QApplication(sys.argv)

    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Radial Tree Menu Test")
    window.resize(400, 200)

    # Central widget
    central = QWidget()
    layout = QVBoxLayout()
    central.setLayout(layout)
    window.setCentralWidget(central)

    # Create radial menu widget
    radial_menu = RadialMenuWidget()

    # Build 3-level nested menu structure
    # Level 1: Root menu
    mesh_ops_submenu = [
        RadialMenuItem(label="Decimate", action=lambda: print(
            "✓ Decimate"), icon="🔻"),
        RadialMenuItem(label="Subdivide", action=lambda: print(
            "✓ Subdivide"), icon="🔺"),
        RadialMenuItem(label="Remesh", action=lambda: print(
            "✓ Remesh"), icon="🔄"),
        RadialMenuItem(label="Resample", action=lambda: print(
            "✓ Resample"), icon="⚙"),
    ]

    filters_submenu = [
        RadialMenuItem(label="Smooth", action=lambda: print(
            "✓ Smooth"), icon="～"),
        RadialMenuItem(label="Sharpen", action=lambda: print(
            "✓ Sharpen"), icon="◆"),
        RadialMenuItem(label="Noise", action=lambda: print(
            "✓ Noise"), icon="▓"),
    ]

    advanced_submenu = [
        RadialMenuItem(label="Filters", action=None,
                       icon="🎨", children=filters_submenu),
        RadialMenuItem(label="Boolean", action=lambda: print(
            "✓ Boolean"), icon="∩"),
        RadialMenuItem(label="Retopo", action=lambda: print(
            "✓ Retopo"), icon="📐"),
    ]

    root_menu = [
        RadialMenuItem(label="Mesh Ops", action=None,
                       icon="📦", children=mesh_ops_submenu),
        RadialMenuItem(label="Visibility", action=lambda: print(
            "✓ Visibility"), icon="👁"),
        RadialMenuItem(label="Advanced", action=None,
                       icon="⚙", children=advanced_submenu),
        RadialMenuItem(label="Ghost", action=lambda: print(
            "✓ Ghost"), icon="👻"),
    ]

    radial_menu.set_items(root_menu)

    # Button to show menu
    btn = QPushButton("Show Tree Menu")

    def show_menu():
        # Show at center of button
        btn_center = btn.mapToGlobal(btn.rect().center())
        radial_menu.show_at(btn_center)

    btn.clicked.connect(show_menu)
    layout.addWidget(btn)

    # Status label
    status_label = QPushButton("Status: Ready")
    status_label.setEnabled(False)
    layout.addWidget(status_label)

    # Test info
    info_text = """
Phase 2 Test Scenarios:

1. BRANCH HOVER:
   - Hover over 'Mesh Ops' → should highlight with blue outline
   - Branch indicator '▶' visible on right side
   
2. DWELL TIMER (250ms):
   - Hold cursor over 'Mesh Ops' for 250ms
   - Should auto-enter submenu (show Decimate, Subdivide, etc.)
   
3. EXIT NODE:
   - In submenu, an 'Exit X' node should appear at anchor
   - Hover over it for 250ms to return to parent
   
4. MULTI-LEVEL (3 levels):
   - Root → Advanced → Filters
   - Test navigation through all 3 levels
   - Test exit from each level
   
5. DWELL CANCEL:
   - Hover over branch briefly (<250ms)
   - Move cursor away → should NOT enter submenu
   - Re-hover → timer should restart

Expected Behavior:
- Branch nodes have '▶' indicator
- 250ms dwell to enter/exit submenus
- Menu stack tracks breadcrumb navigation
- Visual feedback during dwell (optional)
"""
    info_btn = QPushButton("ℹ Test Info")
    info_btn.clicked.connect(lambda: print(info_text))
    layout.addWidget(info_btn)

    window.show()

    print("✓ Window displayed - click 'Show Tree Menu' to test")
    return app.exec()


if __name__ == "__main__":
    sys.exit(test_tree_menu())
