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

# Debug mode - show pizza slice highlighting (default: False)
DEBUG_PIZZA_SLICE: bool = False

# Pixels - no selection within this radius (~50% to nodes)
DEAD_ZONE_RADIUS: int = 75
MENU_RADIUS: int = 150              # Pixels - distance from anchor to item centers
# Pixels - hover detection radius for branches/exit
BRANCH_HOVER_RADIUS: int = 20
# Milliseconds - dwell time before submenu entry/exit
BRANCH_DWELL_MS: int = 250
HIGHLIGHT_SCALE: float = 1.15       # Scale factor for highlighted nodes
# Pixels - extra margin around menu radius for widget size
MENU_WIDGET_MARGIN: int = 100

# Minimum time (ms) before key release can close the menu
# Prevents instant close from stray events during show/grab transition
MIN_SHOW_MS: float = 50.0

# Auto-repeat timeout (ms): if no key event arrives within this window
# after seeing auto-repeat, assume key was released.
# OS auto-repeat is typically every 30-50ms; 100ms gives generous margin.
AUTO_REPEAT_TIMEOUT_MS: float = 100.0

# No-repeat fallback (ms): if this long after show_at() we still haven't
# received ANY key event (no keyPress, no keyRelease, no auto-repeat),
# assume the key was tapped and released before the OS repeat delay.
# OS repeat delay is typically 250-500ms; 600ms gives generous margin.
NO_REPEAT_RELEASE_MS: float = 500.0

# Exit node appearance
EXIT_NODE_RADIUS: int = 20          # Pixels - size of exit node circle
EXIT_ICON_FONT_SIZE: int = 7        # Font size for exit icon (✕)

# Branch node appearance (matches exit node size for consistency)
BRANCH_NODE_RADIUS: int = 20        # Pixels - same as EXIT_NODE_RADIUS
BRANCH_DOT_RADIUS: int = 3          # Pixels - center dot size
BRANCH_LABEL_OFFSET: int = 25       # Pixels - distance of label above circle
BRANCH_LABEL_FONT_SIZE: int = 9     # Font size for branch label

# Animation settings
ANIM_DURATION_MS: float = 150.0     # Total animation duration (ms)
ANIM_STAGGER_MS: float = 20.0      # Delay between each item (ms)
ANIM_SCALE_START: float = 0.6      # Starting scale factor
ANIM_FADE_START: float = 0.0       # Starting opacity (0.0 = invisible)

# Highlight animation
HIGHLIGHT_ANIM_MS: float = 100.0    # Duration for highlight transitions
# Extra scale for highlighted (on top of HIGHLIGHT_SCALE)
HIGHLIGHT_SCALE_BONUS: float = 0.05

# Branch transition animation
BRANCH_FADE_OUT_MS: float = 80.0    # Fade out old items when entering branch
BRANCH_FADE_IN_MS: float = 100.0    # Fade in new items when entering branch

# Node appearance (leaf/invoker nodes only)
NODE_PADDING_X: int = 12            # Horizontal padding in squircles
NODE_PADDING_Y: int = 6             # Vertical padding in squircles
NODE_CORNER_RADIUS: int = 8         # Corner radius for squircles
NODE_FONT_SIZE: int = 9             # Normal node font size
NODE_FONT_SIZE_HIGHLIGHT: int = 10  # Highlighted node font size

# Text outline for better visibility
TEXT_OUTLINE_WIDTH: float = 2.0     # Width of text outline in pixels
TEXT_OUTLINE_COLOR: str = "#000000"  # Black outline for contrast

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
    # True if this is an exit node (requires dwell to activate)
    is_exit: bool = False

    @property
    def is_branch(self) -> bool:
        """Return True if this node has children (branch node)."""
        return self.children is not None and len(self.children) > 0

    @property
    def is_leaf(self) -> bool:
        """Return True if this node has no children and not an exit node."""
        return not self.is_branch and not self.is_exit


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
        leaf_angles: List of leaf node angles (need not be sorted)

    Returns:
        List of (lower_bound, upper_bound) tuples for each leaf
    """
    if not leaf_angles:
        return []

    n = len(leaf_angles)

    # Special case: single leaf covers full 360°
    if n == 1:
        # Return (0, 360) means all angles match this leaf
        # We use (0, 0) with special handling in angle_in_slice
        return [(0.0, 360.0)]

    # Sort leaves by angle to find adjacent neighbors correctly
    sorted_indices = sorted(range(n), key=lambda i: leaf_angles[i])
    sorted_angles = [leaf_angles[i] for i in sorted_indices]

    boundaries: list[tuple[float, float]] = [None] * n  # Pre-allocate

    for sorted_i in range(n):
        original_i = sorted_indices[sorted_i]
        prev_sorted = (sorted_i - 1) % n
        next_sorted = (sorted_i + 1) % n

        prev_angle = sorted_angles[prev_sorted]
        curr_angle = sorted_angles[sorted_i]
        next_angle = sorted_angles[next_sorted]

        # Calculate bisecting angles
        # Lower bound: midpoint between previous and current
        # Handle wrap-around correctly
        diff_prev = curr_angle - prev_angle
        if diff_prev < 0:
            diff_prev += 360
        lower = prev_angle + diff_prev / 2
        if lower >= 360:
            lower -= 360

        # Upper bound: midpoint between current and next
        diff_next = next_angle - curr_angle
        if diff_next < 0:
            diff_next += 360
        upper = curr_angle + diff_next / 2
        if upper >= 360:
            upper -= 360

        boundaries[original_i] = (lower, upper)

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
    # Normalize all angles to 0-360
    angle = angle % 360
    lower = lower % 360
    upper = upper % 360

    # Special case: full circle (single leaf)
    if lower == 0 and upper == 0:
        return True  # All angles match

    result = False
    if lower < upper:
        # Normal case: no wrap-around
        result = lower <= angle < upper
    elif lower > upper:
        # Wrap-around case: slice crosses 0°
        result = angle >= lower or angle < upper
    else:
        # lower == upper: degenerate case, should not happen with proper calculation
        result = False

    return result


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

    # Cursor direction vector (normalized)
    cursor_dx = dx / distance
    cursor_dy = dy / distance

    # Find which slice contains cursor
    for i, (lower, upper) in enumerate(slice_boundaries):
        if angle_in_slice(cursor_angle, lower, upper):
            # Additional check: reject if item is >90° away from cursor (dot product < 0)
            # Item direction vector at its angle
            item_angle = leaf_angles[i]
            item_angle_rad = math.radians(item_angle)
            # Convert to our coordinate system (0° = up, clockwise)
            item_dx = math.sin(item_angle_rad)
            item_dy = -math.cos(item_angle_rad)

            # Dot product: reject if negative (>90° away)
            dot = cursor_dx * item_dx + cursor_dy * item_dy
            if dot >= 0:
                return i

    return None


def distribute_node_angles(nodes: list[RadialMenuItem]) -> list[float]:
    """
    Assign angles to nodes: use explicit if specified, else distribute evenly.

    When angle is not specified (None), nodes are evenly distributed around
    the full 360° circle. First auto node starts at 0° (up), subsequent nodes
    proceed clockwise.

    Args:
        nodes: List of menu items

    Returns:
        List of angles (one per node)
    """
    n = len(nodes)
    if n == 0:
        return []

    # Count how many nodes need auto-distribution
    auto_indices: list[int] = []
    explicit_angles: dict[int, float] = {}

    for i, node in enumerate(nodes):
        if node.angle is not None:
            explicit_angles[i] = node.angle
        else:
            auto_indices.append(i)

    # If all nodes have explicit angles, just return them
    if not auto_indices:
        return [nodes[i].angle for i in range(n)]

    # Distribute auto nodes evenly across 360° based on TOTAL node count
    # This ensures even spacing regardless of explicit angles
    angle_step = 360.0 / n

    angles: list[float] = []
    for i in range(n):
        if i in explicit_angles:
            angles.append(explicit_angles[i])
        else:
            # Node index determines its position in the even distribution
            angles.append(i * angle_step)

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


def draw_text_with_outline(
    painter: 'QPainter',
    rect: 'QRectF',
    alignment: 'Qt.AlignmentFlag',
    text: str,
    text_color: str,
    outline_color: str = TEXT_OUTLINE_COLOR,
    outline_width: float = TEXT_OUTLINE_WIDTH,
) -> None:
    """
    Draw text with an outline for better visibility on any background.

    Args:
        painter: QPainter instance
        rect: Rectangle to draw text in
        alignment: Text alignment flags
        text: Text string to draw
        text_color: Color for the text
        outline_color: Color for the outline (default: black)
        outline_width: Width of the outline in pixels
    """
    # Save current painter state
    painter.save()

    # Get font metrics for accurate positioning
    font = painter.font()
    metrics = painter.fontMetrics()

    # Calculate text position based on alignment
    # addText() uses baseline positioning, so we need to calculate carefully
    text_width = metrics.horizontalAdvance(text)
    text_height = metrics.height()
    ascent = metrics.ascent()

    # Calculate X position
    if alignment & Qt.AlignHCenter:
        x = rect.center().x() - text_width / 2
    elif alignment & Qt.AlignRight:
        x = rect.right() - text_width
    else:  # AlignLeft
        x = rect.left()

    # Calculate Y position (baseline, not top)
    if alignment & Qt.AlignVCenter:
        # Center vertically: middle of rect, adjust for text metrics
        y = rect.center().y() + ascent / 2 - metrics.descent()
    elif alignment & Qt.AlignBottom:
        y = rect.bottom() - metrics.descent()
    else:  # AlignTop
        y = rect.top() + ascent

    # Create a path from the text at the calculated position
    path = QPainterPath()
    path.addText(x, y, font, text)

    # Draw outline
    painter.setPen(QPen(QColor(outline_color), outline_width, Qt.SolidLine,
                        Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)
    painter.drawPath(path)

    # Draw text fill
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(QColor(text_color)))
    painter.drawPath(path)

    # Restore painter state
    painter.restore()


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

            # Phase 2: Tree navigation state
            # Navigation breadcrumb
            self._menu_stack: list[list[RadialMenuItem]] = []
            # Anchor positions for each level
            self._anchor_stack: list[QPoint] = []
            self._hovered_branch_item: RadialMenuItem | None = None
            self._dwell_timer: QTimer = QTimer(self)
            self._dwell_timer.setSingleShot(True)
            self._dwell_timer.timeout.connect(self._on_dwell_timeout)

            # Hover debounce: track if cursor spawned on top of a node
            self._cursor_has_left_spawn_item: bool = True  # Start True for root menu
            # Track label of branch we exited from
            self._just_exited_from_label: str | None = None

            # Key release tracking
            self._keys_currently_pressed: set[int] = set()
            self._trigger_keycode: int | None = None  # Qt keycode for the trigger key
            # Time-based guard: don't close for first N ms after show
            self._show_time: float = 0.0
            # Auto-repeat timeout: track last key event to detect release
            self._last_key_event_time: float = 0.0
            self._seen_auto_repeat: bool = False

            # Cursor tracking for drawing live cursor line
            self._last_cursor_widget_pos: QPointF | None = None

            # Timer for polling cursor position (backup when mouseMoveEvent not firing)
            self._cursor_poll_timer: QTimer = QTimer(self)
            self._cursor_poll_timer.setInterval(16)  # ~60fps
            self._cursor_poll_timer.timeout.connect(self._poll_cursor)

            # Geometry cache
            self._leaf_angles: list[float] = []
            self._slice_boundaries: list[tuple[float, float]] = []
            self._node_angles: list[float] = []

            # Animation state
            self._anim_start_time: float = 0.0  # Timestamp when animation started
            self._anim_active: bool = False      # Is animation currently running

            # Highlight animation state
            self._highlight_anim_start: float = 0.0
            self._prev_highlighted_index: int | None = None
            self._highlight_anim_active: bool = False

            # Branch transition animation state
            self._branch_transition_start: float = 0.0
            self._branch_transition_active: bool = False
            # True if exiting, False if entering
            self._branch_transition_exiting: bool = False

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

        def set_geometry_params(
            self,
            dead_zone_radius: int | None = None,
            menu_radius: int | None = None,
            branch_hover_radius: int | None = None,
            branch_dwell_ms: int | None = None,
        ) -> None:
            """
            Update geometry parameters from settings.

            This allows runtime configuration without modifying module constants.
            Note: Parameters update module-level constants which affect all instances.

            Args:
                dead_zone_radius: Dead zone radius in pixels
                menu_radius: Menu radius in pixels
                branch_hover_radius: Branch hover detection radius in pixels
                branch_dwell_ms: Dwell time in milliseconds
            """
            global DEAD_ZONE_RADIUS, MENU_RADIUS, BRANCH_HOVER_RADIUS, BRANCH_DWELL_MS

            if dead_zone_radius is not None:
                DEAD_ZONE_RADIUS = dead_zone_radius
            if menu_radius is not None:
                MENU_RADIUS = menu_radius
            if branch_hover_radius is not None:
                BRANCH_HOVER_RADIUS = branch_hover_radius
            if branch_dwell_ms is not None:
                BRANCH_DWELL_MS = branch_dwell_ms

            # Recalculate geometry with new parameters
            if self._items:
                self._recalculate_geometry()
                self.update()

        def set_trigger_keycode(self, keycode: int | None) -> None:
            """
            Set the Qt keycode of the trigger key used to invoke this menu.

            This allows the widget to specifically wait for the trigger key's
            release before closing, rather than closing on any key release.

            Args:
                keycode: Qt keycode (e.g., Qt.Key_X), or None for fallback behavior
            """
            self._trigger_keycode = keycode

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

            # Reset key press state for new menu invocation
            import time as _time
            self._keys_currently_pressed.clear()
            self._show_time = _time.monotonic()
            self._last_key_event_time = self._show_time
            self._seen_auto_repeat = False
            print(
                f"[RadialMenu] show_at: trigger=0x{self._trigger_keycode:04X}" if self._trigger_keycode else "[RadialMenu] show_at: trigger=None")

            # Start animation
            self._anim_start_time = _time.monotonic()
            self._anim_active = True

            # Reset branch transition (new menu opened)
            self._branch_transition_active = False

            # Size widget to cover menu area (with some margin)
            size = (MENU_RADIUS + MENU_WIDGET_MARGIN) * 2
            self.setFixedSize(size, size)

            # Position so anchor is at widget center
            self.move(pos.x() - size // 2, pos.y() - size // 2)

            # CRITICAL: Show and activate widget BEFORE grabbing keyboard
            self.show()
            self.raise_()
            self.activateWindow()  # Force window activation
            self.setFocus(Qt.ActiveWindowFocusReason)  # Force focus

            # Grab keyboard immediately to receive key events
            # Do NOT call processEvents() here - it can cause timing issues
            self.grabKeyboard()

            # Start cursor polling timer for smooth cursor line updates
            self._cursor_poll_timer.start()

            # Initialize cursor position
            from PySide6.QtGui import QCursor
            cursor_widget = self.mapFromGlobal(QCursor.pos())
            self._last_cursor_widget_pos = QPointF(cursor_widget)

            self.update()

        def hide_and_invoke(self) -> None:
            """Hide menu and invoke currently highlighted action if any."""
            # Stop cursor polling
            self._cursor_poll_timer.stop()

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
        # Phase 2: Tree Navigation Methods
        # ---------------------------------------------------------------------

        def _is_cursor_over_branch(self, cursor: QPoint, branch_item: RadialMenuItem) -> bool:
            """Check if cursor is within hover radius of a branch or exit node."""
            if not (branch_item.is_branch or branch_item.is_exit):
                return False

            # Get center of widget
            center = QPointF(self.width() / 2, self.height() / 2)

            # Exit nodes are at center, not at MENU_RADIUS
            if branch_item.is_exit:
                branch_pos = center
            else:
                # Get branch node position
                try:
                    item_index = self._items.index(branch_item)
                    angle = self._node_angles[item_index]
                    branch_pos = get_node_position(angle, MENU_RADIUS, center)
                except (ValueError, IndexError):
                    return False

            # Convert cursor to widget coords
            cursor_widget = self.mapFromGlobal(cursor)

            # Calculate distance
            dx = cursor_widget.x() - branch_pos.x()
            dy = cursor_widget.y() - branch_pos.y()
            dist_sq = dx * dx + dy * dy

            return dist_sq <= (BRANCH_HOVER_RADIUS * BRANCH_HOVER_RADIUS)

        def _start_dwell_timer(self, branch_item: RadialMenuItem) -> None:
            """Start dwell timer to enter submenu after delay."""
            self._hovered_branch_item = branch_item
            self._dwell_timer.start(BRANCH_DWELL_MS)
            self.update()  # Repaint to show highlight

        def _cancel_dwell_timer(self) -> None:
            """Cancel dwell timer when cursor leaves branch hover region."""
            self._dwell_timer.stop()
            # Note: Don't clear _hovered_branch_item here - let caller decide
            # This allows exit nodes to remain highlighted during activation

        def _on_dwell_timeout(self) -> None:
            """Handle dwell timer timeout - enter submenu or invoke exit action."""
            if not self._hovered_branch_item:
                return

            # Exit node - invoke its action (which calls _exit_submenu)
            if self._hovered_branch_item.is_exit:
                # Force repaint to show highlight before action
                self.update()
                QApplication.processEvents()
                self._hovered_branch_item.action()
                return

            # Branch node - enter submenu
            if self._hovered_branch_item.children:
                # Force repaint to show highlight before transition
                self.update()
                QApplication.processEvents()
                self._enter_submenu(self._hovered_branch_item)

        def _enter_submenu(self, branch_item: RadialMenuItem) -> None:
            """Push submenu onto stack and display it."""
            if not branch_item.children:
                return

            # Start branch transition animation (fade out)
            import time as _time
            self._branch_transition_start = _time.monotonic()
            self._branch_transition_active = True
            self._branch_transition_exiting = False  # Entering branch

            # Calculate branch node's screen position to use as new anchor
            center = QPointF(self.width() / 2, self.height() / 2)
            try:
                item_index = self._items.index(branch_item)
                angle = self._node_angles[item_index]
                branch_pos_widget = get_node_position(
                    angle, MENU_RADIUS, center)
                # Convert to screen coordinates
                new_anchor = self.mapToGlobal(branch_pos_widget.toPoint())
            except (ValueError, IndexError):
                # Fallback: keep current anchor if branch not found
                new_anchor = self._anchor

            # Push current menu state onto stack
            self._menu_stack.append(self._items)
            if self._anchor:
                self._anchor_stack.append(self._anchor)

            # Update anchor to branch node's position
            self._anchor = new_anchor

            # Reposition widget to center on new anchor
            size = (MENU_RADIUS + MENU_WIDGET_MARGIN) * 2
            self.move(new_anchor.x() - size // 2, new_anchor.y() - size // 2)

            # Cursor spawned on branch node, so it will be over exit node at center
            # Don't trigger exit until cursor leaves and re-enters
            self._cursor_has_left_spawn_item = False

            # Clear just_exited tracking - we're in a new menu context now
            self._just_exited_from_label = None

            # Stop any ongoing dwell timer from parent menu
            self._cancel_dwell_timer()

            # Create exit node and add to submenu items
            exit_node = self._create_exit_node()
            # Exit node stays at center (no angle needed)

            # Set new items from branch children + exit node
            self._items = [exit_node] + list(branch_item.children)
            self._highlighted_leaf_index = None
            self._hovered_branch_item = None  # Clear parent menu hover state

            # Restart appear animation for new items
            self._anim_start_time = _time.monotonic()
            self._anim_active = True

            # Reset cursor position to current global cursor in new widget coords
            # This prevents the cursor line from being offset after widget moves
            from PySide6.QtGui import QCursor
            cursor_widget = self.mapFromGlobal(QCursor.pos())
            self._last_cursor_widget_pos = QPointF(cursor_widget)

            self._recalculate_geometry()
            self.update()

        def _exit_submenu(self) -> None:
            """Pop submenu from stack and restore parent menu."""
            if not self._menu_stack:
                return

            # Start branch transition animation (fade in)
            import time as _time
            self._branch_transition_start = _time.monotonic()
            self._branch_transition_active = True
            self._branch_transition_exiting = True  # Exiting branch

            # Find which branch in parent we need to debounce
            # The exit node's parent is stored when menu was entered
            exited_branch_label: str | None = None
            if len(self._menu_stack) > 0:
                parent_items = self._menu_stack[-1]
                # Find branch that has our current menu as children
                current_first_non_exit = next(
                    (item for item in self._items if not item.is_exit), None)
                if current_first_non_exit:
                    for parent_item in parent_items:
                        if parent_item.is_branch and parent_item.children:
                            first_child = next(
                                (c for c in parent_item.children), None)
                            if first_child and first_child.label == current_first_non_exit.label:
                                exited_branch_label = parent_item.label
                                break

            # Restore parent menu
            self._items = self._menu_stack.pop()
            if self._anchor_stack:
                self._anchor = self._anchor_stack.pop()

                # Reposition widget to center on restored anchor
                size = (MENU_RADIUS + MENU_WIDGET_MARGIN) * 2
                self.move(self._anchor.x() - size // 2,
                          self._anchor.y() - size // 2)

            # Track which branch to debounce in parent menu
            self._just_exited_from_label = exited_branch_label

            # Can interact with other items immediately
            self._cursor_has_left_spawn_item = True

            # Stop any ongoing dwell timer from child menu
            self._cancel_dwell_timer()

            self._highlighted_leaf_index = None

            # Restart appear animation for restored items
            self._anim_start_time = _time.monotonic()
            self._anim_active = True
            self._hovered_branch_item = None  # Clear child menu hover state

            # Reset cursor position to current global cursor in new widget coords
            # This prevents the cursor line from being offset after widget moves
            from PySide6.QtGui import QCursor
            cursor_widget = self.mapFromGlobal(QCursor.pos())
            self._last_cursor_widget_pos = QPointF(cursor_widget)

            self._recalculate_geometry()
            self.update()

        def _create_exit_node(self) -> RadialMenuItem:
            """Create exit node for returning to parent menu."""
            return RadialMenuItem(
                label="Exit",
                action=self._exit_submenu,
                icon="X",
                is_exit=True,  # Requires dwell to activate
            )

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

            # Draw live cursor line from anchor to cursor
            self._draw_cursor_line(painter, center)

            # Phase 2.3: Draw connection strings (cursor → anchor chain)
            self._draw_connection_strings(painter, center)

            # Draw sector slices and labels
            self._draw_sectors(painter, center)

        def _draw_dead_zone(self, painter: QPainter, center: QPointF) -> None:
            """Draw the dead zone indicator in the center."""
            # Draw small center dot instead of large circle
            dot_radius = 4
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(COLOR_TEXT_MUTED)))
            painter.drawEllipse(center, dot_radius, dot_radius)

        def _draw_cursor_line(self, painter: QPainter, center: QPointF) -> None:
            """Draw a live line from anchor to current cursor position."""
            if self._last_cursor_widget_pos is None:
                return

            # Draw line from center to cursor
            pen = QPen(QColor(COLOR_ACCENT))
            pen.setWidth(2)
            pen.setStyle(Qt.SolidLine)
            painter.setPen(pen)
            painter.drawLine(center, self._last_cursor_widget_pos)

            # Draw small circle at cursor position
            cursor_dot_radius = 6
            painter.setBrush(QBrush(QColor(COLOR_ACCENT)))
            painter.drawEllipse(self._last_cursor_widget_pos,
                                cursor_dot_radius, cursor_dot_radius)

        def _draw_connection_strings(self, painter: QPainter, center: QPointF) -> None:
            """Draw dotted lines showing anchor chain (for multi-level menus)."""
            if not self._anchor_stack:
                # No parent menus, no strings to draw
                return

            # Get cursor position in widget coords (we'll draw from cursor to anchors)
            # For now, just draw from current anchor to parent anchors
            # Multi-segment: current anchor ╌╌ parent1 ╌╌ parent2 ╌╌ root

            pen = QPen(QColor(COLOR_TEXT_MUTED))
            pen.setWidth(1)
            pen.setStyle(Qt.DotLine)  # Dotted line
            painter.setPen(pen)

            # Draw lines from current anchor back through the stack
            prev_anchor = center  # Current menu anchor (widget center)
            for parent_anchor in reversed(self._anchor_stack):
                # Convert parent anchor (screen coords) to widget coords
                parent_widget = self.mapFromGlobal(parent_anchor)
                painter.drawLine(prev_anchor, QPointF(parent_widget))
                prev_anchor = QPointF(parent_widget)

        def _draw_sectors(self, painter: QPainter, center: QPointF) -> None:
            """Draw sector slices with highlighting."""
            if not self._node_angles:
                return

            # Calculate animation progress
            import time as _time
            anim_progress = self._get_animation_progress()

            # Calculate branch transition opacity (affects entire menu)
            branch_opacity = self._get_branch_transition_opacity()

            # Get leaf nodes
            leaf_nodes = [item for item in self._items if item.is_leaf]

            for i, item in enumerate(self._items):
                # Calculate per-item animation (staggered by angle)
                angle = self._node_angles[i] if i < len(
                    self._node_angles) else 0
                item_delay = (angle / 360.0) * ANIM_STAGGER_MS
                item_progress = self._ease_out_cubic(
                    max(0.0, min(1.0, (anim_progress * ANIM_DURATION_MS -
                        item_delay) / ANIM_DURATION_MS))
                )

                # Calculate animation transforms
                scale = ANIM_SCALE_START + \
                    (1.0 - ANIM_SCALE_START) * item_progress
                opacity = ANIM_FADE_START + \
                    (1.0 - ANIM_FADE_START) * item_progress

                # Apply branch transition opacity (global fade)
                opacity *= branch_opacity

                # Skip drawing if not yet visible
                if opacity <= 0.0:
                    continue

                # Save painter state for opacity
                painter.save()
                painter.setOpacity(opacity)

                # Exit nodes are drawn at center (anchor), not at MENU_RADIUS
                if item.is_exit:
                    pos = center  # Exit node at center
                else:
                    pos = get_node_position(angle, MENU_RADIUS, center)

                # Determine if this node is highlighted
                is_highlighted = False
                leaf_index_for_anim = None  # Track leaf index for animation
                # Leaf nodes: highlight via pizza slice selection
                if item.is_leaf:
                    leaf_index = leaf_nodes.index(item)
                    leaf_index_for_anim = leaf_index
                    is_highlighted = (
                        leaf_index == self._highlighted_leaf_index)
                # Branch/exit nodes: highlight if being hovered (dwell in progress)
                elif (item.is_branch or item.is_exit) and item == self._hovered_branch_item:
                    is_highlighted = True

                # Apply highlight animation scale (only for leaf nodes)
                highlight_scale = 1.0
                if item.is_leaf:
                    highlight_scale = self._get_highlight_scale(
                        leaf_index_for_anim, is_highlighted)
                scale *= highlight_scale

                # Draw pizza slice background for highlighted leaf (DEBUG only)
                if DEBUG_PIZZA_SLICE and is_highlighted and item.is_leaf and self._slice_boundaries:
                    leaf_index = leaf_nodes.index(item)
                    lower, upper = self._slice_boundaries[leaf_index]
                    self._draw_pizza_slice(painter, center, lower, upper)

                # Branch nodes get special rendering as circles (matching exit nodes)
                if item.is_branch:
                    # Draw branch node as a circle (same size as exit node)
                    branch_radius = BRANCH_NODE_RADIUS * scale
                    if is_highlighted:
                        painter.setPen(QPen(QColor(COLOR_ACCENT), 3))
                        painter.setBrush(QBrush(QColor(COLOR_BG_PRIMARY)))
                    else:
                        painter.setPen(QPen(QColor(COLOR_BORDER), 2))
                        painter.setBrush(QBrush(QColor(COLOR_BG_PRIMARY)))
                    painter.drawEllipse(pos, branch_radius, branch_radius)

                    # Draw icon in center if present, otherwise draw center dot
                    if item.icon:
                        # Draw icon in center (similar to exit node)
                        icon_font = QFont("Arial", EXIT_ICON_FONT_SIZE,
                                          QFont.Bold if is_highlighted else QFont.Normal)
                        painter.setFont(icon_font)
                        painter.setPen(
                            QColor(COLOR_ACCENT if is_highlighted else COLOR_TEXT_MUTED))
                        text_rect = QRectF(pos.x() - branch_radius, pos.y() - branch_radius,
                                           branch_radius * 2, branch_radius * 2)
                        painter.drawText(text_rect, Qt.AlignCenter, item.icon)
                    else:
                        # Draw center dot if no icon
                        painter.setPen(Qt.NoPen)
                        painter.setBrush(QBrush(
                            QColor(COLOR_ACCENT if is_highlighted else COLOR_TEXT_MUTED)))
                        painter.drawEllipse(
                            pos, BRANCH_DOT_RADIUS, BRANCH_DOT_RADIUS)

                    # Draw label above circle (without icon - icon is in circle now)
                    # Always bold for better visibility with outline
                    label_font = QFont(
                        "Arial", BRANCH_LABEL_FONT_SIZE, QFont.Bold)
                    painter.setFont(label_font)
                    label_y = pos.y() - BRANCH_LABEL_OFFSET
                    label_rect = QRectF(pos.x() - 50, label_y - 10, 100, 20)
                    draw_text_with_outline(
                        painter, label_rect, Qt.AlignCenter, item.label,
                        COLOR_ACCENT if is_highlighted else COLOR_TEXT_PRIMARY
                    )
                    painter.restore()  # Restore opacity
                    continue  # Skip normal squircle rendering

                # Exit nodes get special rendering as a circle at center
                if item.is_exit:
                    # Draw exit node as a circle (not squircle)
                    exit_radius = EXIT_NODE_RADIUS * scale
                    if is_highlighted:
                        painter.setPen(QPen(QColor(COLOR_ACCENT), 3))
                        painter.setBrush(QBrush(QColor(COLOR_BG_PRIMARY)))
                    else:
                        painter.setPen(QPen(QColor(COLOR_BORDER), 2))
                        painter.setBrush(QBrush(QColor(COLOR_BG_PRIMARY)))
                    painter.drawEllipse(pos, exit_radius, exit_radius)

                    # Draw X icon in center
                    font = QFont("Arial", EXIT_ICON_FONT_SIZE,
                                 QFont.Bold if is_highlighted else QFont.Normal)
                    painter.setFont(font)
                    painter.setPen(
                        QColor(COLOR_ACCENT if is_highlighted else COLOR_TEXT_MUTED))
                    text_rect = QRectF(pos.x() - exit_radius, pos.y() - exit_radius,
                                       exit_radius * 2, exit_radius * 2)
                    painter.drawText(text_rect, Qt.AlignCenter,
                                     item.icon if item.icon else "✕")
                    painter.restore()  # Restore opacity
                    continue  # Skip normal squircle rendering

                # Prepare text and font
                if is_highlighted:
                    font = QFont("Arial", NODE_FONT_SIZE_HIGHLIGHT, QFont.Bold)
                else:
                    font = QFont("Arial", NODE_FONT_SIZE)
                painter.setFont(font)

                # Icon if present
                text = item.icon + " " if item.icon else ""
                text += item.label

                # Measure text to size squircle
                metrics = painter.fontMetrics()
                text_width = metrics.horizontalAdvance(text)
                text_height = metrics.height()

                # Squircle dimensions with padding
                squircle_width = text_width + NODE_PADDING_X * 2
                squircle_height = text_height + NODE_PADDING_Y * 2
                corner_radius = NODE_CORNER_RADIUS

                # Scale up if highlighted, and apply animation scale
                final_scale = scale
                if is_highlighted:
                    final_scale *= HIGHLIGHT_SCALE

                squircle_width *= final_scale
                squircle_height *= final_scale

                # Draw squircle (rounded rectangle)
                squircle_rect = QRectF(
                    pos.x() - squircle_width / 2,
                    pos.y() - squircle_height / 2,
                    squircle_width,
                    squircle_height
                )

                if is_highlighted:
                    painter.setPen(QPen(QColor(COLOR_ACCENT), 2))
                    painter.setBrush(QBrush(QColor(COLOR_BG_PRIMARY)))
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

                # Restore opacity
                painter.restore()

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

        def _get_animation_progress(self) -> float:
            """Get current animation progress (0.0 to 1.0)."""
            if not self._anim_active:
                return 1.0

            import time as _time
            elapsed_ms = (_time.monotonic() - self._anim_start_time) * 1000.0
            progress = elapsed_ms / ANIM_DURATION_MS
            return min(1.0, progress)

        def _get_highlight_anim_progress(self) -> float:
            """Get current highlight animation progress (0.0 to 1.0)."""
            if not self._highlight_anim_active:
                return 1.0

            import time as _time
            elapsed_ms = (_time.monotonic() -
                          self._highlight_anim_start) * 1000.0
            progress = elapsed_ms / HIGHLIGHT_ANIM_MS
            return min(1.0, progress)

        def _get_highlight_scale(self, item_index: int, is_highlighted: bool) -> float:
            """Calculate animated scale for highlight transitions."""
            # No animation needed if no transition
            if not self._highlight_anim_active:
                return 1.0

            progress = self._get_highlight_anim_progress()
            eased = self._ease_out_cubic(progress)

            # Check if this item is transitioning
            was_highlighted = (self._prev_highlighted_index == item_index)

            if was_highlighted and not is_highlighted:
                # Fading out highlight: 1.0 + bonus → 1.0
                return 1.0 + HIGHLIGHT_SCALE_BONUS * (1.0 - eased)
            elif not was_highlighted and is_highlighted:
                # Fading in highlight: 1.0 → 1.0 + bonus
                return 1.0 + HIGHLIGHT_SCALE_BONUS * eased

            return 1.0  # No transition for this item

        def _get_branch_transition_progress(self) -> float:
            """Get current branch transition animation progress (0.0 to 1.0)."""
            if not self._branch_transition_active:
                return 1.0

            import time as _time
            elapsed_ms = (_time.monotonic() -
                          self._branch_transition_start) * 1000.0
            duration = BRANCH_FADE_OUT_MS if not self._branch_transition_exiting else BRANCH_FADE_IN_MS
            progress = elapsed_ms / duration
            return min(1.0, progress)

        def _get_branch_transition_opacity(self) -> float:
            """Calculate opacity for branch transition (fade out then fade in)."""
            if not self._branch_transition_active:
                return 1.0

            progress = self._get_branch_transition_progress()
            eased = self._ease_out_cubic(progress)

            # Always fade in (items appear from 0 to 1)
            return eased

        @staticmethod
        def _ease_out_cubic(t: float) -> float:
            """Cubic ease-out function for smooth animation."""
            return 1.0 - pow(1.0 - t, 3)

        def _poll_cursor(self) -> None:
            """Poll cursor position every frame for smooth cursor line updates.

            Called by timer since mouseMoveEvent may not fire when cursor
            moves over transparent areas or during 3DCoat viewport interactions.

            Also checks if all keys have been released and closes menu when they are.
            """
            if not self.isVisible() or not self._anchor:
                return

            from PySide6.QtGui import QCursor

            # Get global cursor position
            cursor_screen = QCursor.pos()

            # Convert to widget coordinates
            cursor_widget = self.mapFromGlobal(cursor_screen)
            self._last_cursor_widget_pos = QPointF(cursor_widget)

            # Update animations and request repaint if any are active
            any_anim_active = False

            if self._anim_active:
                progress = self._get_animation_progress()
                if progress >= 1.0:
                    self._anim_active = False
                else:
                    any_anim_active = True

            if self._highlight_anim_active:
                progress = self._get_highlight_anim_progress()
                if progress >= 1.0:
                    self._highlight_anim_active = False
                else:
                    any_anim_active = True

            if self._branch_transition_active:
                progress = self._get_branch_transition_progress()
                if progress >= 1.0:
                    self._branch_transition_active = False
                else:
                    any_anim_active = True

            if any_anim_active:
                self.update()  # Trigger repaint for animation frame

            # Auto-repeat timeout: detect key release by absence of key events
            # Once we've seen auto-repeat events, if they stop arriving for
            # AUTO_REPEAT_TIMEOUT_MS, the key was released.
            if self._seen_auto_repeat:
                import time as _time
                since_last_key: float = (
                    _time.monotonic() - self._last_key_event_time) * 1000
                if since_last_key >= AUTO_REPEAT_TIMEOUT_MS:
                    elapsed_ms: float = (
                        _time.monotonic() - self._show_time) * 1000
                    print(f"[RadialMenu] Auto-repeat timeout: {since_last_key:.0f}ms "
                          f"since last key event, closing (elapsed={elapsed_ms:.0f}ms)")
                    self.hide_and_invoke()
                    return
            else:
                # No-repeat fallback: if enough time passed without ANY key
                # event (no press, no release, no auto-repeat), the key was
                # likely tapped and released before the OS repeat delay kicked
                # in. In 3DCoat's embedded Qt, the initial keyDown goes to
                # 3DCoat (which triggers the script), and if the key is
                # released before auto-repeat starts, keyReleaseEvent may
                # never fire either. This fallback catches that case.
                import time as _time
                elapsed_ms: float = (
                    _time.monotonic() - self._show_time) * 1000
                if elapsed_ms >= NO_REPEAT_RELEASE_MS:
                    print(f"[RadialMenu] No-repeat fallback: {elapsed_ms:.0f}ms "
                          f"elapsed with no key events, assuming key released")
                    self.hide_and_invoke()
                    return

            # Trigger repaint to update cursor line
            self.update()

        def mouseMoveEvent(self, event):
            """Track cursor position and update highlighting."""
            if not self._anchor:
                super().mouseMoveEvent(event)
                return

            # Convert to screen coordinates (use position() instead of deprecated pos())
            cursor_screen = self.mapToGlobal(event.position().toPoint())

            # Track cursor position in widget coords for drawing the live cursor line
            self._last_cursor_widget_pos = QPointF(event.position())

            # Phase 2: Check for branch or exit node hover
            hovered_branch: RadialMenuItem | None = None
            for item in self._items:
                # Branch nodes and exit nodes both require dwell
                if (item.is_branch or item.is_exit) and self._is_cursor_over_branch(cursor_screen, item):
                    hovered_branch = item
                    break

            # Hover debounce: track if cursor has left the spawn item
            if not hovered_branch and not self._cursor_has_left_spawn_item:
                # Cursor left the item we spawned on top of
                self._cursor_has_left_spawn_item = True

            # Clear just-exited tracking when cursor leaves that item
            if self._just_exited_from_label and (not hovered_branch or hovered_branch.label != self._just_exited_from_label):
                self._just_exited_from_label = None

            # Handle dwell timer state
            if hovered_branch:
                # Check if this is the item we just exited from - needs debounce
                if self._just_exited_from_label and hovered_branch.label == self._just_exited_from_label:
                    # Don't trigger until cursor leaves and comes back
                    pass
                # Only start dwell if cursor has left spawn item at least once
                elif self._cursor_has_left_spawn_item:
                    # Start or continue dwell timer
                    if self._hovered_branch_item != hovered_branch:
                        self._start_dwell_timer(hovered_branch)
                # else: cursor still on spawn item, ignore hover
            else:
                # Cancel dwell timer if cursor left branch region
                if self._hovered_branch_item is not None:
                    self._cancel_dwell_timer()
                    self._hovered_branch_item = None  # Clear hover state
                    self.update()  # Repaint to remove highlight

            # Get highlighted leaf (only if not hovering over branch/exit and we have leaves)
            old_highlight = self._highlighted_leaf_index
            if not hovered_branch and self._leaf_angles:
                self._highlighted_leaf_index = get_highlighted_leaf(
                    cursor_screen,
                    self._anchor,
                    self._leaf_angles,
                    self._slice_boundaries,
                )
            else:
                # Don't highlight leaves when hovering over branch/exit or no leaves exist
                self._highlighted_leaf_index = None

            # Emit signal and repaint if changed
            if old_highlight != self._highlighted_leaf_index:
                if self._highlighted_leaf_index is not None:
                    self.highlightChanged.emit(self._highlighted_leaf_index)

                # Start highlight animation transition
                import time as _time
                self._highlight_anim_start = _time.monotonic()
                self._highlight_anim_active = True
                self._prev_highlighted_index = old_highlight

                self.update()

            super().mouseMoveEvent(event)

        def keyReleaseEvent(self, event):
            """
            Handle key release events.

            Close menu on key release if past minimum show time.
            Note: In 3DCoat's embedded Qt, this may never fire for the
            trigger key. Auto-repeat timeout in _poll_cursor is the
            primary detection mechanism.
            """
            # Ignore auto-repeat key events
            if event.isAutoRepeat():
                return

            import time as _time
            key: int = event.key()
            elapsed_ms: float = (_time.monotonic() - self._show_time) * 1000

            # Debug: log every key release
            trigger_str: str = f"0x{self._trigger_keycode:04X}" if self._trigger_keycode else "None"
            print(f"[RadialMenu] KEY_RELEASE: key=0x{key:04X}, "
                  f"trigger={trigger_str}, elapsed={elapsed_ms:.0f}ms, "
                  f"pressed={self._keys_currently_pressed}")

            # Update timing
            self._last_key_event_time = _time.monotonic()

            # Remove from pressed keys set
            if key in self._keys_currently_pressed:
                self._keys_currently_pressed.remove(key)

            # Close if past minimum show time (prevents instant close from stray events)
            if elapsed_ms >= MIN_SHOW_MS:
                print(
                    f"[RadialMenu] Closing on key release after {elapsed_ms:.0f}ms")
                self.hide_and_invoke()
            else:
                print(
                    f"[RadialMenu] Ignoring release, too soon ({elapsed_ms:.0f}ms < {MIN_SHOW_MS}ms)")

        def keyPressEvent(self, event):
            """Handle key press events."""
            import time as _time
            key: int = event.key()
            is_auto: bool = event.isAutoRepeat()

            # Update timing for ALL key events (including auto-repeat)
            self._last_key_event_time = _time.monotonic()

            # Track auto-repeat detection
            if is_auto:
                if not self._seen_auto_repeat:
                    self._seen_auto_repeat = True
                    print(f"[RadialMenu] First auto-repeat detected for key=0x{key:04X}, "
                          f"enabling release-by-timeout detection")
                # Don't track auto-repeat in pressed set, but DO update timing
                return

            # Debug: log non-auto-repeat key presses
            print(f"[RadialMenu] KEY_PRESS: key=0x{key:04X}, "
                  f"pressed={self._keys_currently_pressed}")

            # Track pressed keys
            self._keys_currently_pressed.add(key)

            # Escape always closes immediately
            if key == Qt.Key_Escape:
                self._cursor_poll_timer.stop()
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
