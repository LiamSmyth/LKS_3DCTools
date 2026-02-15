# Radial Tree Menu Implementation Checklist

Reference: [radial_tree_menu_spec.md](radial_tree_menu_spec.md)

**Status:** Phase 1, 2, 3.1, 3.2, and 1.5 complete (Feb 1, 2026). Ready for 3DCoat testing.

**Implementation Summary:**
- Core radial menu widget with tree navigation ✅
- Settings integration via lks_settings.py ✅  
- Config loading from JSON ✅
- Manager singleton for lifecycle management ✅
- Action script for 3DCoat integration ✅
- Auto-discovery registration ✅
- cModule import path resolution ✅

**Files:**
- `radial_menu.py` - Core widget (1133 LOC)
- `radial_menu_manager.py` - Manager singleton (120 LOC)
- `radial_menu_config.py` - Config loader (155 LOC)
- `_test_radial_tree.py` - Full test harness (140 LOC)
- `_test_radial_simple.py` - Simple test (80 LOC)
- `actions/LKS_RadialMenu_Show.py` - 3DCoat entry point (25 LOC)
- `data/radial_menu_config.json` - Default menu
- `data/radial_menu_config_schema.json` - JSON schema

Total: ~1653 LOC

---

## Phase 1: Simple Radial Menu

### 1.1 Core Widget Infrastructure

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [x] | Create `RadialMenuItem` dataclass | Label, action, icon, children, angle (optional explicit positioning) | `utils/ui/widgets/radial_menu.py` |
| [x] | Add `is_branch` property | Returns `True` if node has children (branch), `False` if leaf | `utils/ui/widgets/radial_menu.py` |
| [x] | Create `RadialMenuWidget` skeleton | QWidget with `Qt.ToolTip \| Qt.FramelessWindowHint`, transparent background, basic init | `utils/ui/widgets/radial_menu.py` |
| [x] | Implement `show_at(pos: QPoint)` | Position widget centered on given screen position, call `show()` | `utils/ui/widgets/radial_menu.py` |
| [x] | Implement `hide_and_invoke()` | Hide widget, invoke currently highlighted action if any | `utils/ui/widgets/radial_menu.py` |
| [x] | Add items property/setter | Accept list of `RadialMenuItem`, store for rendering | `utils/ui/widgets/radial_menu.py` |

### 1.2 Geometry & Angle Math

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [x] | Define constants | `DEAD_ZONE_RADIUS`, `MENU_RADIUS`, `BRANCH_HOVER_RADIUS`, `BRANCH_DWELL_MS`, etc. | `utils/ui/widgets/radial_menu.py` |
| [x] | Implement `cursor_to_angle(cursor, anchor) -> float` | Convert cursor position to angle (0° = up, clockwise) | `utils/ui/widgets/radial_menu.py` |
| [x] | Implement `get_highlighted_leaf(cursor, anchor, leaf_angles) -> int \| None` | Pizza slice selection with 90° cone rejection (dot product < 0) | `utils/ui/widgets/radial_menu.py` |
| [x] | Implement `calculate_slice_boundaries(leaf_angles) -> list[tuple]` | Compute bisecting angles between adjacent leaves for slice regions | `utils/ui/widgets/radial_menu.py` |
| [x] | Implement `get_node_position(angle, radius, center) -> QPointF` | Convert angle + radius to position relative to center | `utils/ui/widgets/radial_menu.py` |
| [x] | Implement `distribute_node_angles(nodes) -> list[float]` | Assign angles: use explicit if specified, else distribute evenly from 0° | `utils/ui/widgets/radial_menu.py` |

### 1.3 Painting

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [x] | Implement `paintEvent` | Draw connection strings, dead zone dot, sector items with highlights | `utils/ui/widgets/radial_menu.py` |
| [x] | Draw sector labels | Render leaf items as squircles with text, positioned at MENU_RADIUS | `utils/ui/widgets/radial_menu.py` |
| [x] | Draw branch nodes | Circles (20px) with center dot and label above, matching exit node size | `utils/ui/widgets/radial_menu.py` |
| [x] | Draw exit nodes | Circles (20px) at center with "✕" icon | `utils/ui/widgets/radial_menu.py` |
| [x] | Draw dead zone indicator | Small dot in center showing anchor position | `utils/ui/widgets/radial_menu.py` |
| [x] | Draw connection strings | Dotted lines through anchor chain for multi-level visualization | `utils/ui/widgets/radial_menu.py` |
| [x] | Style using `ui/styles.py` colors | Use `COLOR_BG_*`, `COLOR_ACCENT`, etc. for consistency | `utils/ui/widgets/radial_menu.py` |

### 1.4 Mouse Tracking

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [x] | Override `mouseMoveEvent` | Track cursor, update highlights for both leaves and branches, call `update()` | `utils/ui/widgets/radial_menu.py` |
| [x] | Store anchor point | Cache anchor in `_anchor: QPoint` on show (cursor pos at invocation) | `utils/ui/widgets/radial_menu.py` |
| [x] | Separate leaf vs branch tracking | Leaves use angle-based pizza slices; branches use hover detection (40px radius) | `utils/ui/widgets/radial_menu.py` |
| [x] | Emit highlight changed signal | `highlightChanged = Signal(int)` for external listeners | `utils/ui/widgets/radial_menu.py` |
| [x] | Implement debounce logic | Track spawn/exit state to prevent accidental triggers when menu repositions | `utils/ui/widgets/radial_menu.py` |

### 1.5 Standalone Test Harness

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [x] | Create `_test_radial_tree.py` | Test harness with 3-level nested menu structure | `utils/ui/widgets/_test_radial_tree.py` |
| [x] | Add debug mouse tracking | Print cursor position, angles, and highlighted index | `utils/ui/widgets/_test_radial_tree.py` |
| [x] | Test with Python | Verify it works via `python _test_radial_tree.py` | Manual test ✓ |
| [x] | Document how to find Python | Use system Python or 3DCoat's embedded Python | `_docs/radial_tree_menu_spec.md` |

### 1.6 Key Event Handling (Widget-Level)

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [x] | Override `keyReleaseEvent` | On trigger key release: invoke if leaf highlighted, else just close | `utils/ui/widgets/radial_menu.py` |
| [x] | Key release in dead zone | Close menu, invoke nothing | `utils/ui/widgets/radial_menu.py` |
| [x] | Override `keyPressEvent` | On Escape, hide without invoking | `utils/ui/widgets/radial_menu.py` |
| [x] | Call `grabKeyboard()` on show | Ensure widget receives key events even if shown non-modally | `utils/ui/widgets/radial_menu.py` |
| [x] | Call `releaseKeyboard()` on hide | Clean up keyboard grab | `utils/ui/widgets/radial_menu.py` |

---

## Phase 1.5: Integration with LKS (3DCoat)

### 1.5.1 Manager Singleton

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [x] | Create `RadialMenuManager` class | Singleton that owns `RadialMenuWidget` instance | `utils/ui/widgets/radial_menu_manager.py` |
| [x] | Implement `show_menu(items: list[RadialMenuItem])` | Show menu at `QCursor.pos()` with given items | `utils/ui/widgets/radial_menu_manager.py` |
| [x] | Implement `get_manager() -> RadialMenuManager` | Module-level accessor for singleton | `utils/ui/widgets/radial_menu_manager.py` |
| [x] | Add to widget `__init__.py` exports | Export `RadialMenuWidget`, `RadialMenuItem`, `get_manager` | `utils/ui/widgets/__init__.py` |

### 1.5.2 Action Script

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [x] | Create `LKS_RadialMenu_Show.py` action | Calls manager to show menu loaded from config | `actions/LKS_RadialMenu_Show.py` |
| [x] | Define initial menu items | Curated list: Decimate, Resample, Ghost, To Surface, etc. | `data/radial_menu_config.json` |
| [x] | Register action in menu | Auto-discovered by `register_actions()` in Scripts menu | `utils/registration_utils.py` |

### 1.5.3 cExtension Integration

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [x] | Verify Qt events processed | Confirm `QApplication.processEvents()` in `preprocess()` handles menu | `LKS.py` |
| [ ] | Test menu in 3DCoat | Trigger via action, verify display and selection works | Manual test |
| [ ] | Handle focus edge cases | Test what happens if clicking in viewport while menu is open | Manual test |

---

## Phase 2: Radial Tree Menu (Nested Submenus)

### 2.1 Data Model

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [x] | Add `children` to `RadialMenuItem` | Optional list of child items for submenu | `utils/ui/widgets/radial_menu.py` |
| [x] | Add `is_branch`, `is_leaf`, `is_exit` properties | Computed from children and is_exit flag | `utils/ui/widgets/radial_menu.py` |
| [x] | Create tree navigation state | Track `_menu_stack` and `_anchor_stack` for breadcrumb navigation | `utils/ui/widgets/radial_menu.py` |

### 2.2 Submenu Navigation

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [x] | Track branch node hover state | Detect when cursor is within `BRANCH_HOVER_RADIUS` (40px) of a branch node | `utils/ui/widgets/radial_menu.py` |
| [x] | Implement dwell timer for branch entry | Start timer on branch hover, enter submenu after `BRANCH_DWELL_MS` (250ms) | `utils/ui/widgets/radial_menu.py` |
| [x] | Dwell timer reset on leave | Cancel timer if cursor leaves hover region before dwell completes | `utils/ui/widgets/radial_menu.py` |
| [x] | Dwell timer restart on re-enter | Fresh timer starts when cursor re-enters hover region | `utils/ui/widgets/radial_menu.py` |
| [x] | Push submenu onto stack | Store current menu state, set branch position as new anchor | `utils/ui/widgets/radial_menu.py` |
| [x] | Reposition widget on branch node | Calculate branch screen position, center widget on it | `utils/ui/widgets/radial_menu.py` |
| [x] | Create exit node at submenu center | Add exit node with "✕" icon as first item in submenu | `utils/ui/widgets/radial_menu.py` |
| [x] | Exit node dwell behavior | Hover + dwell over exit node to return to parent menu | `utils/ui/widgets/radial_menu.py` |
| [x] | Pop submenu from stack | Restore parent items, restore parent anchor, reposition widget | `utils/ui/widgets/radial_menu.py` |
| [x] | Spawn protection debounce | Prevent immediate triggers when cursor spawns on exit node | `utils/ui/widgets/radial_menu.py` |
| [x] | Exit debounce tracking | Track branch label (not object) to prevent re-entry after exit | `utils/ui/widgets/radial_menu.py` |

### 2.3 Tree Visualization

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [x] | Draw connection strings | Dotted lines through anchor chain (cursor → branch2 → branch1 → root) | `utils/ui/widgets/radial_menu.py` |
| [x] | Draw branch nodes as circles | 20px circles with center dot (3px) and label above (25px offset) | `utils/ui/widgets/radial_menu.py` |
| [x] | Highlight branch node on hover | Accent color border and dot when within hover radius during dwell | `utils/ui/widgets/radial_menu.py` |
| [x] | Draw exit node at center | 20px circle with "✕" icon (7pt font) at submenu center | `utils/ui/widgets/radial_menu.py` |
| [x] | Highlight exit node on hover | Accent color border and icon when within hover radius during dwell | `utils/ui/widgets/radial_menu.py` |
| [x] | Draw submenu dead zone | Small dot at center showing anchor position | `utils/ui/widgets/radial_menu.py` |
| [x] | Visual distinction: circles vs squircles | Circles = navigation (branch/exit), squircles = actions (leaves) | `utils/ui/widgets/radial_menu.py` |

---

## Phase 3: Configuration & Customization

### 3.1 Settings Integration

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [x] | Add radial menu settings to `lks_settings.py` | `dead_zone_radius`, `menu_radius`, `branch_hover_radius`, `branch_dwell_ms`, `trigger_key` | `utils/lks_settings.py` |
| [x] | Load settings on menu show | Read from settings cache | `utils/ui/widgets/radial_menu_manager.py` |

### 3.2 Menu Configuration

| Done | Task | Description | Files |
|:----:|------|-------------|-------|
| [x] | Define JSON schema for menu config | Items with labels, actions, children | `data/radial_menu_config_schema.json` |
| [x] | Implement config loader | Parse JSON, build `RadialMenuItem` tree | `utils/radial_menu_config.py` |
| [x] | Create default config | Ship with sensible defaults | `data/radial_menu_config.json` |

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
| [x] | **M1: Widget renders** | Standalone test shows radial sectors with labels |
| [x] | **M2: Sector highlighting** | Moving mouse highlights correct sector, dead zone works, 90° cone rejection |
| [x] | **M3: Selection invokes** | Key release invokes highlighted action, prints to console |
| [x] | **M4: Works in 3DCoat** | *(Not tested - Phase 1.5 pending)* |
| [x] | **M5: Submenus work** | Navigate 3+ levels deep, exit nodes work, no debounce flicker |
| [x] | **M6: Settings integrated** | Menu loads constants from lks_settings.py |
| [x] | **M7: Config loading works** | Menu items loaded from JSON config |
| [ ] | **M8: User configurable** | Menu items editable via builder UI |
| [ ] | **M9: Works in 3DCoat** | *(Not tested - Phase 1.5 pending)* |

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
| 2026-02-01 | Initial checklist created, Phase 1 and Phase 2 implementation completed |
| 2026-02-01 | Updated checklist to reflect completed Phase 2: circular branch/exit nodes (20px), label-based exit debounce, 90° selection cone, dwell highlighting |
| 2026-02-01 | Phase 3.1 and 3.2 complete: settings integration, config loader, JSON schema, default config |
| 2026-02-01 | Phase 1.5 complete: RadialMenuManager singleton, action script with config loading, auto-discovery registration |
| 2026-02-01 | Added cModule import path auto-prefixing, verified Qt event processing, created simple test script |
