"""
LKS External Panel Application.

A standalone DearPyGui panel that communicates with 3DCoat
via IPC files. Runs in a separate process to avoid blocking the viewport.
"""
from __future__ import annotations

import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import dearpygui.dearpygui as dpg

from .ipc_client import IPCClient


# =============================================================================
# LOGGING
# =============================================================================

LOG_FILE: Path = Path(__file__).parent.parent / "lks_panel_log.txt"


def log(message: str) -> None:
    """Write a message to the log file."""
    timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [app] {message}\n")
    except Exception:
        pass


def log_exception(context: str) -> None:
    """Log the current exception with full traceback."""
    log(f"EXCEPTION in {context}:")
    log(traceback.format_exc())


# =============================================================================
# CONSTANTS
# =============================================================================

WINDOW_WIDTH: int = 380
WINDOW_HEIGHT: int = 550
POLL_INTERVAL_SEC: float = 0.2  # How often to poll for updates
APP_TITLE: str = "LKS Tools Panel"


# =============================================================================
# APPLICATION STATE
# =============================================================================

class AppState:
    """Application state container."""

    def __init__(self) -> None:
        self.client: IPCClient = IPCClient()
        self.is_connected: bool = False
        self.elements: List[Dict[str, Any]] = []
        self.selected_element: Optional[str] = None
        self.last_poll_time: float = 0.0


_state: AppState = AppState()


# =============================================================================
# UI CALLBACKS
# =============================================================================

def on_refresh_clicked() -> None:
    """Refresh the scene elements list."""
    refresh_elements()


def on_element_selected(sender: int, app_data: Any) -> None:
    """Handle element selection in the listbox."""
    global _state
    if app_data:
        _state.selected_element = app_data
        update_element_info()


def on_select_in_3dcoat() -> None:
    """Select the current element in 3DCoat."""
    global _state
    if _state.selected_element:
        result: bool = _state.client.select_element(_state.selected_element)
        if result:
            update_status(f"Selected: {_state.selected_element}")
        else:
            update_status("Failed to select element")


def on_ghost_toggle() -> None:
    """Toggle ghost state of selected element."""
    global _state
    if _state.selected_element:
        # Find current ghost state
        current_ghost: bool = False
        for el in _state.elements:
            if el.get("name") == _state.selected_element:
                current_ghost = el.get("ghosted", False)
                break

        result: bool = _state.client.ghost_element(
            _state.selected_element, not current_ghost)
        if result:
            update_status(
                f"{'Ghosted' if not current_ghost else 'Unghosted'}: {_state.selected_element}")
            refresh_elements()
        else:
            update_status("Failed to toggle ghost")


def on_hide_toggle() -> None:
    """Toggle visibility of selected element."""
    global _state
    if _state.selected_element:
        # Find current visibility
        current_visible: bool = True
        for el in _state.elements:
            if el.get("name") == _state.selected_element:
                current_visible = el.get("visible", True)
                break

        result: bool = _state.client.hide_element(
            _state.selected_element, current_visible)
        if result:
            update_status(
                f"{'Hidden' if current_visible else 'Shown'}: {_state.selected_element}")
            refresh_elements()
        else:
            update_status("Failed to toggle visibility")


def run_quick_action(action_name: str) -> None:
    """Execute a quick action script."""
    global _state
    update_status(f"Running: {action_name}...")
    result: bool = _state.client.run_action(action_name)
    if result:
        update_status(f"Done: {action_name}")
        refresh_elements()
    else:
        update_status(f"Failed: {action_name}")


def on_unghost_all() -> None:
    """Unghost all elements."""
    run_quick_action("SculptObject_Unghost_All")


def on_decimate_half() -> None:
    """Decimate selected to half."""
    run_quick_action("SculptObject_Decimate_Half_Selected")


def on_to_surface() -> None:
    """Convert all to surface mode."""
    run_quick_action("SculptObject_ToSurface_All")


def on_scale_down() -> None:
    """Scale down selected 100x."""
    run_quick_action("SculptObject_Scale_Down100x_Selected")


# =============================================================================
# UI UPDATE FUNCTIONS
# =============================================================================

def update_connection_status() -> None:
    """Update the connection status indicator."""
    global _state
    _state.is_connected = _state.client.is_connected()

    if dpg.does_item_exist("connection_status"):
        if _state.is_connected:
            dpg.set_value("connection_status", "Connected")
            dpg.configure_item("connection_status", color=(100, 255, 100))
        else:
            dpg.set_value("connection_status", "Disconnected")
            dpg.configure_item("connection_status", color=(255, 100, 100))


def update_status(message: str) -> None:
    """Update the status bar message."""
    if dpg.does_item_exist("status_text"):
        dpg.set_value("status_text", message)


def update_element_info() -> None:
    """Update the element info display."""
    global _state

    if not dpg.does_item_exist("element_info"):
        return

    if not _state.selected_element:
        dpg.set_value("element_info", "No element selected")
        return

    # Find element data
    for el in _state.elements:
        if el.get("name") == _state.selected_element:
            info_lines: List[str] = [
                f"Name: {el.get('name', 'Unknown')}",
                f"Visible: {el.get('visible', True)}",
                f"Ghosted: {el.get('ghosted', False)}",
                f"Polys: {el.get('polycount', 0):,}",
            ]
            dpg.set_value("element_info", "\n".join(info_lines))
            return

    dpg.set_value("element_info", f"Element: {_state.selected_element}")


def refresh_elements() -> None:
    """Refresh the elements list from 3DCoat."""
    global _state

    elements: Optional[List[Dict[str, Any]]] = _state.client.list_elements()

    if elements is None:
        update_status("Failed to get elements")
        return

    _state.elements = elements

    # Build display names with state indicators
    names: List[str] = []
    for el in elements:
        name: str = el.get("name", "Unknown")
        indicators: List[str] = []
        if el.get("ghosted"):
            indicators.append("[G]")
        if not el.get("visible", True):
            indicators.append("[H]")
        suffix: str = " " + "".join(indicators) if indicators else ""
        names.append(f"{name}{suffix}")

    # Update the listbox
    if dpg.does_item_exist("elements_listbox"):
        dpg.configure_item("elements_listbox", items=names)

    update_status(f"Loaded {len(elements)} elements")


def poll_updates() -> None:
    """Poll for updates from 3DCoat."""
    global _state

    current_time: float = time.time()
    if current_time - _state.last_poll_time < POLL_INTERVAL_SEC:
        return

    _state.last_poll_time = current_time

    # Check for shutdown request
    if _state.client.is_shutdown_requested():
        dpg.stop_dearpygui()
        return

    # Update connection status
    update_connection_status()

    # Poll for any pending results
    _state.client.poll_results()


# =============================================================================
# MAIN APPLICATION
# =============================================================================

def create_ui() -> None:
    """Create the main UI."""
    dpg.create_context()

    # Apply a dark theme
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 10)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)

    dpg.bind_theme(global_theme)

    # Create main window
    with dpg.window(label=APP_TITLE, tag="main_window", width=WINDOW_WIDTH, height=WINDOW_HEIGHT):

        # === Connection Status Header ===
        with dpg.group(horizontal=True):
            dpg.add_text("Status: ")
            dpg.add_text("Checking...", tag="connection_status",
                         color=(255, 255, 100))
            dpg.add_spacer(width=50)
            dpg.add_button(label="Refresh",
                           callback=on_refresh_clicked, width=70)

        dpg.add_separator()
        dpg.add_spacer(height=5)

        # === Scene Elements Section ===
        dpg.add_text("Scene Elements", color=(150, 200, 255))
        dpg.add_spacer(height=3)

        dpg.add_listbox(
            tag="elements_listbox",
            items=[],
            num_items=10,
            callback=on_element_selected,
            width=-1
        )

        dpg.add_spacer(height=5)

        # Element info
        dpg.add_text("No element selected", tag="element_info",
                     wrap=WINDOW_WIDTH - 40)

        dpg.add_spacer(height=5)

        # Element action buttons
        with dpg.group(horizontal=True):
            dpg.add_button(label="Select in 3DC",
                           callback=on_select_in_3dcoat, width=100)
            dpg.add_button(label="Ghost", callback=on_ghost_toggle, width=70)
            dpg.add_button(label="Hide", callback=on_hide_toggle, width=70)

        dpg.add_separator()
        dpg.add_spacer(height=5)

        # === Quick Actions Section ===
        dpg.add_text("Quick Actions", color=(150, 200, 255))
        dpg.add_spacer(height=3)

        with dpg.group(horizontal=True):
            dpg.add_button(label="Unghost All",
                           callback=on_unghost_all, width=110)
            dpg.add_button(label="Decimate 50%",
                           callback=on_decimate_half, width=110)

        dpg.add_spacer(height=3)

        with dpg.group(horizontal=True):
            dpg.add_button(label="To Surface All",
                           callback=on_to_surface, width=110)
            dpg.add_button(label="Scale Down 100x",
                           callback=on_scale_down, width=110)

        dpg.add_separator()
        dpg.add_spacer(height=5)

        # === Status Bar ===
        dpg.add_text("Ready", tag="status_text", color=(180, 180, 180))

    # Configure viewport
    dpg.create_viewport(
        title=APP_TITLE,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        resizable=True,
        always_on_top=True
    )

    dpg.setup_dearpygui()
    dpg.show_viewport()

    # Set the main window as primary
    dpg.set_primary_window("main_window", True)


def run_main_loop() -> None:
    """Run the main application loop."""
    # Initial connection check and refresh
    update_connection_status()
    if _state.is_connected:
        refresh_elements()

    # Main loop
    while dpg.is_dearpygui_running():
        poll_updates()
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


def main() -> None:
    """Main entry point."""
    log("app.main() called")
    try:
        log("Creating UI...")
        create_ui()
        log("UI created, entering main loop...")
        run_main_loop()
        log("Main loop exited")
    except Exception:
        log_exception("main()")
        raise


if __name__ == "__main__":
    main()
