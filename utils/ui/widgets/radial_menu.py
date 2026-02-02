"""
Radial menu widget - Phase 1: Simple radial menu.

A direction-based menu that appears at cursor position. Users move mouse
in a direction to select an action, then release trigger key to invoke.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
import math

try:
    from PySide6.QtCore import Qt, QPoint, QPointF, Signal, QTimer, QRectF
    from PySide6.QtWidgets import QWidget, QApplication
    from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
    HAS_QT = True
except ImportError:
    HAS_QT = False

# Try to import colors from LKS styles
try:
    from utils.ui.styles import (
        COLOR_BG_PRIMARY,
        COLOR_BG_SECONDARY,
        COLOR_TEXT_PRIMARY,
        COLOR_TEXT_MUTED,
        COLOR_ACCENT,
        COLOR_BORDER,
    )
except ImportError:
    # Fallback colors if styles module not available
    COLOR_BG_PRIMARY = "#2b2b2b"
    COLOR_BG_SECONDARY = "#1e1e1e"
    COLOR_TEXT_PRIMARY = "#e0e0e0"
    COLOR_TEXT_MUTED = "#888888"
    COLOR_ACCENT = "#90caf9"
    COLOR_BORDER = "#555555"

# =============================================================================
# CONSTANTS
# =============================================================================

# Pixels - no selection within this radius (~50% to nodes)
DEAD_ZONE_RADIUS: int = 75
MENU_RADIUS: int = 150              # Pixels - distance from anchor to item centers
BRANCH_HOVER_RADIUS: int = 40       # Pixels - hover detection radius for branches
# Milliseconds - dwell time to enter/exit submenu
BRANCH_DWELL_MS: int = 250

# =============================================================================
# DATA MODEL
# =============================================================================


@dataclass
class RadialMenuItem:
    """Single item in a radial menu."""
    label: str
    action: Callable[[], None]
    icon: str | None = None
    children: list[RadialMenuItem] | None = None
    angle: float | None = None  # Optional explicit angle (0° = up, clockwise)

    @property
    def is_branch(self) -> bool:
        """Return True if this node has children (branch node)."""
        return self.children is not None and len(self.children) > 0

    @property
    def is_leaf(self) -> bool:
        """Return True if this node has no children (leaf node)."""
        return not self.is_branch


# =============================================================================
# GEOMETRY & ANGLE MATH
# =============================================================================

def cursor_to_angle(cursor: QPoint, anchor: QPoint) -> float:
    """
    Convert cursor position to angle in degrees.

    0° = up (12 o'clock), angles increase clockwise.

    Args:
        cursor: Current cursor position
        anchor: Anchor point (menu center)

    Returns:
        Angle in degrees (0-360)
    """
    dx: float = cursor.x() - anchor.x()
    dy: float = cursor.y() - anchor.y()

    # atan2 gives angle from positive X axis, counter-clockwise
    # We want angle from negative Y axis (up), clockwise
    angle_rad = math.atan2(dx, -dy)
    angle_deg = math.degrees(angle_rad)

    # Normalize to 0-360
    if angle_deg < 0:
        angle_deg += 360

    return angle_deg


def calculate_slice_boundaries(leaf_angles: list[float]) -> list[tuple[float, float]]:
    """
    Calculate pizza slice boundaries for each leaf node.

    Boundaries are the bisecting angles between adjacent leaves.

    Args:
        leaf_angles: Sorted list of leaf node angles

    Returns:
        List of (lower_bound, upper_bound) tuples for each leaf
    """
    if not leaf_angles:
        return []

    n = len(leaf_angles)
    boundaries: list[tuple[float, float]] = []

    for i in range(n):
        prev_angle = leaf_angles[i - 1] if i > 0 else leaf_angles[-1]
        curr_angle = leaf_angles[i]
        next_angle = leaf_angles[(i + 1) % n]

        # Calculate bisecting angles
        # Lower bound: midpoint between previous and current
        if prev_angle > curr_angle:
            # Wrap around 360°
            lower = (prev_angle + curr_angle + 360) / 2
            if lower >= 360:
                lower -= 360
        else:
            lower = (prev_angle + curr_angle) / 2

        # Upper bound: midpoint between current and next
        if curr_angle > next_angle:
            # Wrap around 360°
            upper = (curr_angle + next_angle + 360) / 2
            if upper >= 360:
                upper -= 360
        else:
            upper = (curr_angle + next_angle) / 2

        boundaries.append((lower, upper))

    return boundaries


def angle_in_slice(angle: float, lower: float, upper: float) -> bool:
    """
    Check if angle is within a slice boundary.

    Handles wrap-around at 0°/360°.

    Args:
        angle: Angle to test (0-360)
        lower: Lower boundary of slice
        upper: Upper boundary of slice

    Returns:
        True if angle is in slice
    """
    if lower <= upper:
        # Normal case: no wrap-around
        return lower <= angle < upper
    else:
        # Wrap-around case: slice crosses 0°
        return angle >= lower or angle < upper


def get_highlighted_leaf(
    cursor: QPoint,
    anchor: QPoint,
    leaf_angles: list[float],
    slice_boundaries: list[tuple[float, float]],
) -> int | None:
    """
    Get index of highlighted leaf based on cursor position.

    Returns None if cursor is in dead zone or no match.

    Args:
        cursor: Current cursor position
        anchor: Menu anchor point
        leaf_angles: Angles of leaf nodes (sorted)
        slice_boundaries: Slice boundaries for each leaf

    Returns:
        Index of highlighted leaf, or None
    """
    # Check dead zone
    dx = cursor.x() - anchor.x()
    dy = cursor.y() - anchor.y()
    distance = math.sqrt(dx * dx + dy * dy)

    if distance < DEAD_ZONE_RADIUS:
        return None

    # Get cursor angle
    cursor_angle = cursor_to_angle(cursor, anchor)

    # Find which slice contains cursor
    for i, (lower, upper) in enumerate(slice_boundaries):
        if angle_in_slice(cursor_angle, lower, upper):
            return i

    return None


def distribute_node_angles(nodes: list[RadialMenuItem]) -> list[float]:
    """
    Assign angles to nodes: use explicit if specified, else distribute evenly.

    First node at 0° (up), subsequent nodes proceed clockwise.

    Args:
        nodes: List of menu items

    Returns:
        List of angles (one per node)
    """
    angles: list[float] = []
    explicit_count = sum(1 for node in nodes if node.angle is not None)
    auto_count = len(nodes) - explicit_count

    if auto_count > 0:
        # Calculate even distribution for auto nodes
        angle_step = 360.0 / len(nodes)

    auto_index = 0
    for i, node in enumerate(nodes):
        if node.angle is not None:
            # Use explicit angle
            angles.append(node.angle)
        else:
            # Auto-distribute
            angles.append(auto_index * angle_step)
            auto_index += 1

    return angles


def get_node_position(angle: float, radius: float, center: QPointF) -> QPointF:
    """
    Convert angle + radius to screen position relative to center.

    Args:
        angle: Angle in degrees (0° = up, clockwise)
        radius: Distance from center
        center: Center point

    Returns:
        Position as QPointF
    """
    # Convert to radians, adjust for Qt coordinate system
    angle_rad = math.radians(angle)

    # Calculate position (remember: 0° is up, clockwise)
    x = center.x() + radius * math.sin(angle_rad)
    y = center.y() - radius * math.cos(angle_rad)

    return QPointF(x, y)


# =============================================================================
# RADIAL MENU WIDGET
# =============================================================================

if HAS_QT:
    class RadialMenuWidget(QWidget):
        """
        Frameless overlay widget displaying radial menu sectors.

        UX Pattern:
        1. Hold trigger key → menu appears at cursor
        2. Move mouse in direction → sector highlights
        3. Release trigger key → highlighted action invokes
        """

        # Signals
        # Emitted when highlighted sector changes
        highlightChanged = Signal(int)

        def __init__(self, parent=None):
            super().__init__(parent)

            # Window flags for overlay
            self.setWindowFlags(
                Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
            )
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setAttribute(Qt.WA_ShowWithoutActivating)

            # CRITICAL: Make widget receive mouse events even in transparent areas
            # Without this, Qt only sends events when mouse is over painted pixels
            self.setAttribute(Qt.WA_TransparentForMouseEvents,
                              False)  # Explicitly disable
            # Alternative to setMouseTracking
            self.setAttribute(Qt.WA_MouseTracking, True)

            # State
            self._items: list[RadialMenuItem] = []
            self._anchor: QPoint | None = None
            self._highlighted_leaf_index: int | None = None

            # Geometry cache
            self._leaf_angles: list[float] = []
            self._slice_boundaries: list[tuple[float, float]] = []
            self._node_angles: list[float] = []

            # Enable mouse tracking
            self.setMouseTracking(True)

        # ---------------------------------------------------------------------
        # Public API
        # ---------------------------------------------------------------------

        def set_items(self, items: list[RadialMenuItem]) -> None:
            """Set menu items to display."""
            self._items = items
            self._highlighted_leaf_index = None
            self._recalculate_geometry()
            self.update()

        def _recalculate_geometry(self) -> None:
            """Recalculate node positions and slice boundaries."""
            if not self._items:
                self._leaf_angles = []
                self._slice_boundaries = []
                self._node_positions = []
                return

            # Distribute angles
            all_angles = distribute_node_angles(self._items)

            # Extract leaf nodes and their angles
            self._leaf_angles = []
            leaf_angle_list: list[float] = []
            for i, item in enumerate(self._items):
                if item.is_leaf:
                    self._leaf_angles.append(all_angles[i])
                    leaf_angle_list.append(all_angles[i])

            # Calculate slice boundaries for leaves
            self._slice_boundaries = calculate_slice_boundaries(
                leaf_angle_list)

            # Calculate positions (will need center from widget coords)
            # Store angles for now, positions calculated in paint
            self._node_angles = all_angles

        def show_at(self, pos: QPoint) -> None:
            """Show menu centered at given screen position."""
            self._anchor = pos

            # Size widget to cover menu area (with some margin)
            size = (MENU_RADIUS + 100) * 2
            self.setFixedSize(size, size)

            # Position so anchor is at widget center
            self.move(pos.x() - size // 2, pos.y() - size // 2)

            # Grab keyboard to receive key events
            self.grabKeyboard()

            self.show()
            self.raise_()
            self.update()

        def hide_and_invoke(self) -> None:
            """Hide menu and invoke currently highlighted action if any."""
            # Release keyboard grab
            self.releaseKeyboard()

            # Invoke action if a leaf is highlighted
            if self._highlighted_leaf_index is not None:
                leaf_nodes = [item for item in self._items if item.is_leaf]
                if 0 <= self._highlighted_leaf_index < len(leaf_nodes):
                    action = leaf_nodes[self._highlighted_leaf_index].action
                    self.hide()
                    # Invoke after hide to avoid focus issues
                    QTimer.singleShot(0, action)
                    return

            # No action to invoke, just hide
            self.hide()

        # ---------------------------------------------------------------------
        # Event Handlers (Placeholder - will implement in later phases)
        # ---------------------------------------------------------------------

        def paintEvent(self, event):
            """Paint the radial menu."""
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            if not self._anchor or not self._items:
                return

            # Widget center (where anchor is in widget coords)
            center = QPointF(self.width() / 2, self.height() / 2)

            # CRITICAL: Paint a nearly-transparent background over entire widget
            # This ensures Qt sends mouse events to ALL areas, not just visible pixels
            painter.setPen(Qt.NoPen)
            # Almost invisible (alpha=1)
            painter.setBrush(QBrush(QColor(0, 0, 0, 1)))
            painter.drawRect(0, 0, self.width(), self.height())

            # Draw dead zone
            self._draw_dead_zone(painter, center)

            # Draw sector slices and labels
            self._draw_sectors(painter, center)

        def _draw_dead_zone(self, painter: QPainter, center: QPointF) -> None:
            """Draw the dead zone indicator in the center."""
            # Draw small center dot instead of large circle
            dot_radius = 4
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(COLOR_TEXT_MUTED)))
            painter.drawEllipse(center, dot_radius, dot_radius)

        def _draw_sectors(self, painter: QPainter, center: QPointF) -> None:
            """Draw sector slices with highlighting."""
            if not self._node_angles:
                return

            # Get leaf nodes
            leaf_nodes = [item for item in self._items if item.is_leaf]

            for i, item in enumerate(self._items):
                angle = self._node_angles[i]
                pos = get_node_position(angle, MENU_RADIUS, center)

                # Determine if this leaf is highlighted
                is_highlighted = False
                if item.is_leaf:
                    leaf_index = leaf_nodes.index(item)
                    is_highlighted = (
                        leaf_index == self._highlighted_leaf_index)

                # Draw pizza slice background for highlighted leaf
                if is_highlighted and self._slice_boundaries:
                    leaf_index = leaf_nodes.index(item)
                    lower, upper = self._slice_boundaries[leaf_index]
                    self._draw_pizza_slice(painter, center, lower, upper)

                # Prepare text and font
                if is_highlighted:
                    font = QFont("Arial", 10, QFont.Bold)
                else:
                    font = QFont("Arial", 9)
                painter.setFont(font)

                # Icon if present
                text = item.icon + " " if item.icon else ""
                text += item.label

                # Measure text to size squircle
                metrics = painter.fontMetrics()
                text_width = metrics.horizontalAdvance(text)
                text_height = metrics.height()

                # Squircle dimensions with padding
                padding_x = 12
                padding_y = 6
                squircle_width = text_width + padding_x * 2
                squircle_height = text_height + padding_y * 2
                corner_radius = 8

                # Draw squircle (rounded rectangle)
                squircle_rect = QRectF(
                    pos.x() - squircle_width / 2,
                    pos.y() - squircle_height / 2,
                    squircle_width,
                    squircle_height
                )

                if is_highlighted:
                    painter.setPen(QPen(QColor(COLOR_ACCENT), 2))
                    painter.setBrush(
                        QBrush(QColor(COLOR_ACCENT + "40")))  # 25% alpha
                else:
                    painter.setPen(QPen(QColor(COLOR_BORDER), 1))
                    painter.setBrush(QBrush(QColor(COLOR_BG_PRIMARY)))

                painter.drawRoundedRect(
                    squircle_rect, corner_radius, corner_radius)

                # Draw text centered in squircle
                if is_highlighted:
                    painter.setPen(QColor(COLOR_ACCENT))
                else:
                    painter.setPen(QColor(COLOR_TEXT_PRIMARY))

                painter.drawText(squircle_rect, Qt.AlignCenter, text)

                # Draw arrow for branch nodes (Phase 2) - positioned at right edge of squircle
                if item.is_branch:
                    arrow_font = QFont("Arial", 10)
                    painter.setFont(arrow_font)
                    painter.setPen(QColor(COLOR_TEXT_MUTED))
                    arrow_x = squircle_rect.right() + 4
                    arrow_y = squircle_rect.center().y()
                    arrow_rect = QRectF(arrow_x - 8, arrow_y - 8, 16, 16)
                    painter.drawText(arrow_rect, Qt.AlignCenter, "▶")

        def _draw_pizza_slice(
            self,
            painter: QPainter,
            center: QPointF,
            lower_angle: float,
            upper_angle: float,
        ) -> None:
            """Draw a highlighted pizza slice background."""
            painter.setPen(Qt.NoPen)
            painter.setBrush(
                QBrush(QColor(COLOR_ACCENT + "20")))  # 12.5% alpha

            # Create path for pizza slice using our coordinate system throughout
            # Our system: 0° = up, clockwise
            path = QPainterPath()

            # Handle wrap-around for angle calculation
            angle_span = upper_angle - lower_angle
            if angle_span < 0:
                angle_span += 360

            # Draw slice as a series of line segments
            # Start at inner radius (dead zone edge)
            start_inner = get_node_position(
                lower_angle, DEAD_ZONE_RADIUS, center)
            path.moveTo(start_inner)

            # Line to outer radius
            start_outer = get_node_position(
                lower_angle, MENU_RADIUS + 30, center)
            path.lineTo(start_outer)

            # Arc along outer edge (draw as many line segments)
            # One segment per 5 degrees, min 8
            segments = max(int(angle_span / 5), 8)
            for i in range(1, segments + 1):
                angle = lower_angle + (angle_span * i / segments)
                if angle >= 360:
                    angle -= 360
                point = get_node_position(angle, MENU_RADIUS + 30, center)
                path.lineTo(point)

            # Line back to inner radius
            end_inner = get_node_position(
                upper_angle, DEAD_ZONE_RADIUS, center)
            path.lineTo(end_inner)

            # Arc back along inner edge
            for i in range(segments, -1, -1):
                angle = lower_angle + (angle_span * i / segments)
                if angle >= 360:
                    angle -= 360
                point = get_node_position(angle, DEAD_ZONE_RADIUS, center)
                path.lineTo(point)

            path.closeSubpath()
            painter.drawPath(path)

        def mouseMoveEvent(self, event):
            """Track cursor position and update highlighting."""
            if not self._anchor or not self._leaf_angles:
                super().mouseMoveEvent(event)
                return

            # Convert to screen coordinates (use position() instead of deprecated pos())
            cursor_screen = self.mapToGlobal(event.position().toPoint())

            # DEBUG
            import math
            dx = cursor_screen.x() - self._anchor.x()
            dy = cursor_screen.y() - self._anchor.y()
            dist = math.sqrt(dx*dx + dy*dy)
            angle = cursor_to_angle(cursor_screen, self._anchor)
            print(f"Mouse: dx={dx:4.0f} dy={dy:4.0f} dist={dist:4.0f} angle={angle:6.1f} "
                  f"leaf_angles={self._leaf_angles} boundaries={self._slice_boundaries}")

            # Get highlighted leaf
            old_highlight = self._highlighted_leaf_index
            self._highlighted_leaf_index = get_highlighted_leaf(
                cursor_screen,
                self._anchor,
                self._leaf_angles,
                self._slice_boundaries,
            )

            print(f"  -> highlighted_index={self._highlighted_leaf_index}")

            # Emit signal and repaint if changed
            if old_highlight != self._highlighted_leaf_index:
                if self._highlighted_leaf_index is not None:
                    self.highlightChanged.emit(self._highlighted_leaf_index)
                self.update()

            super().mouseMoveEvent(event)

        def keyReleaseEvent(self, event):
            """Handle key release to invoke action."""
            # For now, any key release closes menu
            self.hide_and_invoke()

        def keyPressEvent(self, event):
            """Handle key press events."""
            if event.key() == Qt.Key_Escape:
                self.releaseKeyboard()
                self.hide()


# =============================================================================
# STANDALONE TEST
# =============================================================================

def test_geometry():
    """Test geometry calculations."""
    print("\n" + "="*60)
    print("GEOMETRY TEST - Phase 1.2")
    print("="*60)

    # Test cursor_to_angle
    if HAS_QT:
        anchor = QPoint(100, 100)

        test_cases = [
            (QPoint(100, 50), "Up", 0.0),
            (QPoint(150, 100), "Right", 90.0),
            (QPoint(100, 150), "Down", 180.0),
            (QPoint(50, 100), "Left", 270.0),
        ]

        print("\ncursor_to_angle tests:")
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
    print(f"\nDistribute 4 nodes evenly:")
    for i, angle in enumerate(angles):
        print(f"  Node {i}: {angle:6.1f} deg")

    # Test slice boundaries
    leaf_angles = [0.0, 90.0, 180.0, 270.0]
    boundaries = calculate_slice_boundaries(leaf_angles)
    print(f"\nSlice boundaries for {leaf_angles}:")
    for i, (lower, upper) in enumerate(boundaries):
        print(f"  Slice {i}: {lower:6.1f} to {upper:6.1f} deg")

    # Test angle_in_slice
    print(f"\nangle_in_slice tests:")
    test_angles = [45.0, 135.0, 315.0]
    for test_angle in test_angles:
        for i, (lower, upper) in enumerate(boundaries):
            if angle_in_slice(test_angle, lower, upper):
                print(f"  {test_angle} deg is in slice {i}")
                break

    print("="*60 + "\n")


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

    print("\n" + "="*60)
    print("RADIAL MENU TEST - Phase 1.3 (Painting)")
    print("="*60)
    print("The menu should appear at screen center with:")
    print("  • Dead zone circle in center")
    print("  • Four sectors with icons and labels")
    print("  • Dotted separator lines")
    print("\nMove mouse to highlight sectors.")
    print("Press any key while highlighting to invoke action.")
    print("Press Escape to close without invoking.")
    print("="*60 + "\n")

    sys.exit(app.exec())


if __name__ == "__main__":
    test_standalone()
