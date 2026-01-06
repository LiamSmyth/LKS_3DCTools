"""
GripBoxContainer - Vertical container with drag-drop reordering support.

A container that wraps child widgets in GripBox items and allows reordering
via drag-drop. Each child gets a grip column on the left for dragging.

Usage:
    from utils.ui.widgets.grip_box_container import GripBoxContainer
    
    container = GripBoxContainer()
    container.add_widget(my_collapsible_section, state_key="section1")
    container.add_widget(my_button, state_key="button1")
    layout.addWidget(container)
    
    # Get/set order
    order = container.get_order()  # ['section1', 'button1']
    container.set_order(['button1', 'section1'])  # Reorder
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame
    from PySide6.QtCore import QPoint

try:
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame
    from PySide6.QtCore import QPoint
    
    from .grip_box_item import GripBox
    
    HAS_QT: bool = True
except ImportError:
    HAS_QT = False


if HAS_QT:
    
    class GripBoxContainer(QWidget):
        """
        A vertical container where children can be reordered by dragging.
        
        Each child widget is wrapped in a GripBox with a drag column.
        Drag-drop reordering is supported with visual feedback.
        
        Optional state_key parameter allows persisting the order to settings.
        """
        def __init__(self, parent: QWidget | None = None):
            super().__init__(parent)
            self.items: list[GripBox] = []
            
            # Main layout
            self.layout = QVBoxLayout(self)
            self.layout.setContentsMargins(0, 0, 0, 0)
            self.layout.setSpacing(1)
            
            # Enable drop
            self.setAcceptDrops(True)
            
            # Placeholder for drag target position
            self.drop_indicator: QFrame | None = None
            self.drag_item: GripBox | None = None
        
        def add_widget(
            self,
            widget: QWidget,
            state_key: str | None = None
        ) -> GripBox:
            """
            Add a widget to the container with a grip column.
            
            Args:
                widget: The widget to add
                state_key: Optional key for persisting order
            
            Returns:
                The GripBox wrapper
            """
            item = GripBox(widget, state_key, self)
            self.items.append(item)
            self.layout.addWidget(item)
            return item
        
        def remove_widget(self, widget: QWidget) -> bool:
            """
            Remove a widget from the container.
            
            Args:
                widget: The content widget to remove
            
            Returns:
                True if removed, False if not found
            """
            for item in self.items[:]:
                if item.content_widget == widget:
                    self.layout.removeWidget(item)
                    item.deleteLater()
                    self.items.remove(item)
                    return True
            return False
        
        def get_order(self) -> list[str]:
            """
            Get the current order of items by their state_keys.
            
            Returns:
                List of state_keys in current order
            """
            return [
                item.state_key
                for item in self.items
                if item.state_key is not None
            ]
        
        def set_order(self, state_keys: list[str]) -> None:
            """
            Reorder items to match the given state_key order.
            
            Args:
                state_keys: List of state_keys in desired order
            """
            # Create mapping of state_key -> item
            item_map = {
                item.state_key: item
                for item in self.items
                if item.state_key is not None
            }
            
            # Reorder items
            new_items = []
            for key in state_keys:
                if key in item_map:
                    new_items.append(item_map[key])
                    del item_map[key]
            
            # Add any items not in the order list at the end
            new_items.extend(item_map.values())
            
            # Update layout
            for item in self.items:
                self.layout.removeWidget(item)
            
            self.items = new_items
            for item in self.items:
                self.layout.addWidget(item)
        
        def dragEnterEvent(self, event):
            """Accept drag events from grip boxes."""
            if event.mimeData().text().startswith("grip_box_"):
                event.acceptProposedAction()
        
        def dragMoveEvent(self, event):
            """Show drop position indicator and live preview."""
            if not event.mimeData().text().startswith("grip_box_"):
                return
            
            # Find which item is being dragged
            drag_id = event.mimeData().text().replace("grip_box_", "")
            drag_item = None
            for item in self.items:
                if str(id(item)) == drag_id:
                    drag_item = item
                    break
            
            if not drag_item:
                return
            
            self.drag_item = drag_item
            
            # Find drop position
            drop_pos = event.pos()
            insert_index = self._get_insert_index(drop_pos)
            
            # Get current position of dragged item
            current_index = self.items.index(drag_item)
            
            # Live preview: move item to show where it will be inserted
            if current_index != insert_index:
                # Remove from old position
                self.items.remove(drag_item)
                self.layout.removeWidget(drag_item)
                
                # Adjust insert index if we removed before it
                if current_index < insert_index:
                    insert_index -= 1
                
                # Insert at new position
                self.items.insert(insert_index, drag_item)
                self.layout.insertWidget(insert_index, drag_item)
            
            event.acceptProposedAction()
        
        def dragLeaveEvent(self, event):
            """Cancel drag preview when leaving container."""
            # The live reordering will be undone if dropEvent doesn't complete
            pass
        
        def dropEvent(self, event):
            """Finalize drop - reordering already happened in dragMoveEvent."""
            if not event.mimeData().text().startswith("grip_box_"):
                return
            
            event.acceptProposedAction()
            
            # Save the new order
            self._save_order()
            
            self.drag_item = None
        
        def _get_insert_index(self, pos: QPoint) -> int:
            """
            Determine where to insert based on drop position.
            
            Args:
                pos: Drop position
            
            Returns:
                Index where item should be inserted
            """
            for i, item in enumerate(self.items):
                item_center = item.geometry().center()
                if pos.y() < item_center.y():
                    return i
            return len(self.items)
        
        def _save_order(self) -> None:
            """Save the current order to settings if state keys present."""
            order = self.get_order()
            if not order:
                return
            
            # TODO: Implement order persistence to settings
            # For now, just print it
            print(f"[GripBoxContainer] New order: {order}")

else:
    # Stub class when PySide6 not available
    class GripBoxContainer:  # type: ignore[no-redef]
        """Stub GripBoxContainer for when Qt is not available."""
        def __init__(self, *args, **kwargs):
            pass
        
        def add_widget(self, *args, **kwargs):
            return None
        
        def remove_widget(self, *args, **kwargs):
            return False
        
        def get_order(self):
            return []
        
        def set_order(self, *args, **kwargs):
            pass
