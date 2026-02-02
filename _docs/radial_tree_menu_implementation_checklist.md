# Radial Tree Menu Implementation Checklist

Reference: [radial_tree_menu_spec.md](radial_tree_menu_spec.md)

---

## Phase 1: Simple Radial Menu

### 1.1 Core Widget Infrastructure

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [ ] | Create `RadialMenuItem` dataclass | Label, action, icon, children, angle (optional explicit positioning) | `utils/ui/widgets/radial_menu.py` |
| [ ] | Add `is_branch` property | Returns `True` if node has children (branch), `False` if leaf | `utils/ui/widgets/radial_menu.py` |
| [ ] | Create `RadialMenuWidget` skeleton | QWidget with `Qt.ToolTip \| Qt.FramelessWindowHint`, transparent background, basic init | `utils/ui/widgets/radial_menu.py` |
| [ ] | Implement `show_at(pos: QPoint)` | Position widget centered on given screen position, call `show()` | `utils/ui/widgets/radial_menu.py` |
| [ ] | Implement `hide_and_invoke()` | Hide widget, invoke currently highlighted action if any | `utils/ui/widgets/radial_menu.py` |
| [ ] | Add items property/setter | Accept list of `RadialMenuItem`, store for rendering | `utils/ui/widgets/radial_menu.py` |

### 1.2 Geometry & Angle Math

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [ ] | Define constants | `DEAD_ZONE_RADIUS`, `MENU_RADIUS`, `BRANCH_HOVER_RADIUS`, `BRANCH_DWELL_MS` | `utils/ui/widgets/radial_menu.py` |
| [ ] | Implement `cursor_to_angle(cursor, anchor) -> float` | Convert cursor position to angle (0° = up, clockwise) | `utils/ui/widgets/radial_menu.py` |
| [ ] | Implement `get_highlighted_leaf(cursor, anchor, leaf_angles) -> int \| None` | Pizza slice selection: return leaf index or None if in dead zone | `utils/ui/widgets/radial_menu.py` |
| [ ] | Implement `calculate_slice_boundaries(leaf_angles) -> list[tuple]` | Compute bisecting angles between adjacent leaves for slice regions | `utils/ui/widgets/radial_menu.py` |
| [ ] | Implement `_get_node_position(angle, radius) -> QPointF` | Convert angle + radius to screen position relative to anchor | `utils/ui/widgets/radial_menu.py` |
| [ ] | Implement `distribute_node_angles(nodes) -> list[float]` | Assign angles: use explicit if specified, else distribute evenly from 0° | `utils/ui/widgets/radial_menu.py` |

### 1.3 Painting

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [ ] | Implement `paintEvent` | Draw background circle, sector slices, highlight for selected sector | `utils/ui/widgets/radial_menu.py` |
| [ ] | Draw sector labels | Render item labels at calculated positions, handle text alignment | `utils/ui/widgets/radial_menu.py` |
| [ ] | Draw dead zone indicator | Subtle circle in center showing "no selection" area | `utils/ui/widgets/radial_menu.py` |
| [ ] | Add sector separators | Thin lines between sectors for visual clarity | `utils/ui/widgets/radial_menu.py` |
| [ ] | Style using `ui/styles.py` colors | Use `COLOR_BG_*`, `COLOR_ACCENT`, etc. for consistency | `utils/ui/widgets/radial_menu.py` |

### 1.4 Mouse Tracking

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [ ] | Override `mouseMoveEvent` | Track cursor, update `_highlighted_leaf_index`, call `update()` | `utils/ui/widgets/radial_menu.py` |
| [ ] | Store anchor point | Cache anchor in `_anchor: QPoint` on show (cursor pos at invocation) | `utils/ui/widgets/radial_menu.py` |
| [ ] | Separate leaf vs branch tracking | Leaves use angle-based pizza slices; branches use hover detection | `utils/ui/widgets/radial_menu.py` |
| [ ] | Emit highlight changed signal | `highlightChanged = Signal(int)` for external listeners | `utils/ui/widgets/radial_menu.py` |

### 1.5 Standalone Test Harness

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [ ] | Create `test_standalone()` function | Creates QApplication, shows menu with dummy items, prints selection | `utils/ui/widgets/radial_menu.py` |
| [ ] | Add `if __name__ == "__main__"` block | Call `test_standalone()` when run directly | `utils/ui/widgets/radial_menu.py` |
| [ ] | Test with 3DCoat's Python | Verify it works via `python.exe radial_menu.py` outside 3DCoat | Manual test |
| [ ] | Document how to find 3DCoat Python | Reference existing hotkey editor standalone launch pattern | `_docs/radial_tree_menu_spec.md` |

### 1.6 Key Event Handling (Widget-Level)

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [ ] | Override `keyReleaseEvent` | On trigger key release: invoke if leaf highlighted, else just close | `utils/ui/widgets/radial_menu.py` |
| [ ] | Key release in dead zone | Close menu, invoke nothing | `utils/ui/widgets/radial_menu.py` |
| [ ] | Override `keyPressEvent` | On Escape, hide without invoking | `utils/ui/widgets/radial_menu.py` |
| [ ] | Call `grabKeyboard()` on show | Ensure widget receives key events even if shown non-modally | `utils/ui/widgets/radial_menu.py` |
| [ ] | Call `releaseKeyboard()` on hide | Clean up keyboard grab | `utils/ui/widgets/radial_menu.py` |

---

## Phase 1.5: Integration with LKS (3DCoat)

### 1.5.1 Manager Singleton

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [ ] | Create `RadialMenuManager` class | Singleton that owns `RadialMenuWidget` instance | `utils/ui/widgets/radial_menu_manager.py` |
| [ ] | Implement `show_menu(items: list[RadialMenuItem])` | Show menu at `QCursor.pos()` with given items | `utils/ui/widgets/radial_menu_manager.py` |
| [ ] | Implement `get_manager() -> RadialMenuManager` | Module-level accessor for singleton | `utils/ui/widgets/radial_menu_manager.py` |
| [ ] | Add to widget `__init__.py` exports | Export `RadialMenuWidget`, `RadialMenuItem`, `get_manager` | `utils/ui/widgets/__init__.py` |

### 1.5.2 Action Script

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [ ] | Create `LKS_RadialMenu_Show.py` action | Calls manager to show menu with hardcoded items | `actions/LKS_RadialMenu_Show.py` |
| [ ] | Define initial menu items | Curated list: Decimate, Resample, Ghost, To Surface, etc. | `actions/LKS_RadialMenu_Show.py` |
| [ ] | Register action in menu | Add to Scripts menu via `coat.ui.insertInMenu` | `register_main.py` or `__onstartup.py` |

### 1.5.3 cExtension Integration

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [ ] | Verify Qt events processed | Confirm `QApplication.processEvents()` in `preprocess()` handles menu | `LKS.py` |
| [ ] | Test menu in 3DCoat | Trigger via action, verify display and selection works | Manual test |
| [ ] | Handle focus edge cases | Test what happens if clicking in viewport while menu is open | Manual test |

---

## Phase 2: Radial Tree Menu (Nested Submenus)

### 2.1 Data Model

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [ ] | Add `children` to `RadialMenuItem` | Optional list of child items for submenu | `utils/ui/widgets/radial_menu.py` |
| [ ] | Add `has_children` property | Convenience check for rendering arrow indicator | `utils/ui/widgets/radial_menu.py` |
| [ ] | Create tree navigation state | Track `_menu_stack: list[list[RadialMenuItem]]` for breadcrumb | `utils/ui/widgets/radial_menu.py` |

### 2.2 Submenu Navigation

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [ ] | Track branch node hover state | Detect when cursor is within `BRANCH_HOVER_RADIUS` of a branch node | `utils/ui/widgets/radial_menu.py` |
| [ ] | Implement dwell timer for branch entry | Start timer on branch hover, enter submenu after `BRANCH_DWELL_MS` | `utils/ui/widgets/radial_menu.py` |
| [ ] | Dwell timer reset on leave | Cancel timer if cursor leaves hover region before dwell completes | `utils/ui/widgets/radial_menu.py` |
| [ ] | Dwell timer restart on re-enter | Fresh timer starts when cursor re-enters hover region | `utils/ui/widgets/radial_menu.py` |
| [ ] | Push submenu onto stack | Store current menu state, set branch position as new anchor | `utils/ui/widgets/radial_menu.py` |
| [ ] | Hide parent menu nodes | When entering submenu, hide all parent nodes (keep in memory) | `utils/ui/widgets/radial_menu.py` |
| [ ] | Create exit node at submenu anchor | Branch node becomes exit node with "✕" or "Exit" visual indicator | `utils/ui/widgets/radial_menu.py` |
| [ ] | Exit node dwell behavior | Hover + dwell over exit node to return to parent menu | `utils/ui/widgets/radial_menu.py` |
| [ ] | Pop submenu from stack | Restore parent items visibility, restore parent anchor | `utils/ui/widgets/radial_menu.py` |

### 2.3 Tree Visualization

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [ ] | Draw "string" from cursor to anchor | Dotted/dashed line from current cursor position to current anchor | `utils/ui/widgets/radial_menu.py` |
| [ ] | Draw multi-segment string for nested menus | Chain: cursor ╌╌ branch2 ╌╌ branch1 ╌╌ root | `utils/ui/widgets/radial_menu.py` |
| [ ] | Draw branch node indicator | Small arrow/chevron on branch nodes to show they have children | `utils/ui/widgets/radial_menu.py` |
| [ ] | Highlight branch node on hover | Visual feedback when cursor is within hover radius of branch | `utils/ui/widgets/radial_menu.py` |
| [ ] | Draw exit node in submenu | Render "✕" or "Exit" indicator at submenu anchor position | `utils/ui/widgets/radial_menu.py` |
| [ ] | Highlight exit node on hover | Visual feedback when cursor is within hover radius of exit | `utils/ui/widgets/radial_menu.py` |
| [ ] | Draw submenu dead zone | Visual indicator of inner dead zone ("donut hole") around exit node | `utils/ui/widgets/radial_menu.py` |
| [ ] | Animate transition (optional) | Smooth animation when entering/exiting submenus | `utils/ui/widgets/radial_menu.py` |

---

## Phase 3: Configuration & Customization

### 3.1 Settings Integration

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [ ] | Add radial menu settings to `lks_settings.py` | `dead_zone_radius`, `menu_radius`, `trigger_key` | `utils/lks_settings.py` |
| [ ] | Load settings on menu show | Read from settings cache | `utils/ui/widgets/radial_menu_manager.py` |

### 3.2 Menu Configuration

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [ ] | Define JSON schema for menu config | Items with labels, actions, children | `data/radial_menu_config.json` |
| [ ] | Implement config loader | Parse JSON, build `RadialMenuItem` tree | `utils/radial_menu_config.py` |
| [ ] | Create default config | Ship with sensible defaults | `data/radial_menu_config.json` |

### 3.3 Menu Builder UI (Future)

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [ ] | Design menu builder panel | Qt widget for drag-drop menu customization | `ui/radial_menu_builder.py` |
| [ ] | Implement action picker | List available actions from `action_discovery.py` | `ui/radial_menu_builder.py` |
| [ ] | Implement tree editor | Add/remove/reorder items in radial tree | `ui/radial_menu_builder.py` |
| [ ] | Save/load configurations | Persist to JSON, support multiple presets | `ui/radial_menu_builder.py` |

---

## Testing Milestones

| Done | Milestone | Success Criteria |
|:----:|-----------|------------------|
| [ ] | **M1: Widget renders** | Standalone test shows radial sectors with labels |
| [ ] | **M2: Sector highlighting** | Moving mouse highlights correct sector, dead zone works |
| [ ] | **M3: Selection invokes** | Key release invokes highlighted action, prints to console |
| [ ] | **M4: Works in 3DCoat** | Action triggers menu, selection runs LKS operator |
| [ ] | **M5: Submenus work** | Can navigate into and out of nested menus |
| [ ] | **M6: User configurable** | Menu items loaded from JSON config |

---

## Dependencies

| Package | Required For | Notes |
|---------|--------------|-------|
| PySide6 | All phases | Already in requirements.txt |
| pynput | Backup key handling | Only if Qt event filter unreliable |

---

## Document History

| Date | Change |
|------|--------|
| 2026-02-01 | Initial checklist |
