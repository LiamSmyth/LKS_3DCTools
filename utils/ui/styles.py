"""
LKS UI Styles.

Contains Qt stylesheets and theme definitions for the LKS panel.
Separated from main code for maintainability.

Color constants are defined first, then used to construct the stylesheet dynamically.
"""

# =============================================================================
# COLOR CONSTANTS (for programmatic use and stylesheet construction)
# =============================================================================

# Background colors
COLOR_BG_PRIMARY: str = "#2b2b2b"
COLOR_BG_SECONDARY: str = "#1e1e1e"
COLOR_BG_BUTTON: str = "#404040"
COLOR_BG_BUTTON_HOVER: str = "#4a4a4a"
COLOR_BG_BUTTON_PRESSED: str = "#353535"
COLOR_BG_BUTTON_DISABLED: str = "#333333"
COLOR_BG_HIGHLIGHT: str = "#264f78"
COLOR_BG_TREE_ALT: str = "#252525"
COLOR_BG_HEADER: str = "#383838"
COLOR_BG_TOOLTIP: str = "#3c3c3c"
COLOR_BG_TAB: str = "#353535"
COLOR_BG_TREE_HOVER: str = "#3a3a3a"

# Text colors
COLOR_TEXT_PRIMARY: str = "#e0e0e0"
COLOR_TEXT_MUTED: str = "#888888"
COLOR_TEXT_DISABLED: str = "#666666"

# Accent colors
COLOR_ACCENT: str = "#90caf9"        # Icy blue - primary accent
COLOR_SUCCESS: str = "#81c784"       # Green
COLOR_WARNING: str = "#ffb74d"       # Orange
COLOR_ERROR: str = "#ef5350"         # Red

# Border/separator colors
COLOR_BORDER: str = "#555555"
COLOR_BORDER_LIGHT: str = "#666666"

# Scrollbar colors
COLOR_SCROLLBAR_BG: str = COLOR_BG_PRIMARY
COLOR_SCROLLBAR_HANDLE: str = COLOR_BORDER
COLOR_SCROLLBAR_HANDLE_HOVER: str = COLOR_BORDER_LIGHT

# =============================================================================
# DARK THEME STYLESHEET (dynamically constructed from constants)
# =============================================================================

def _create_dark_stylesheet() -> str:
    """
    Create the dark theme stylesheet using color constants.
    
    This allows colors to be defined once and reused throughout the stylesheet,
    making it easier to maintain and modify the theme.
    """
    return f"""
QWidget {{
    background-color: {COLOR_BG_PRIMARY};
    color: {COLOR_TEXT_PRIMARY};
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 11px;
}}

QGroupBox {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    color: {COLOR_ACCENT};
}}

QPushButton {{
    background-color: {COLOR_BG_BUTTON};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 6px 12px;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {COLOR_BG_BUTTON_HOVER};
    border-color: {COLOR_ACCENT};
}}

QPushButton:pressed {{
    background-color: {COLOR_BG_BUTTON_PRESSED};
}}

QPushButton:disabled {{
    background-color: {COLOR_BG_BUTTON_DISABLED};
    color: {COLOR_TEXT_DISABLED};
}}

QLabel {{
    background-color: transparent;
}}

QTreeWidget {{
    background-color: {COLOR_BG_SECONDARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    alternate-background-color: {COLOR_BG_TREE_ALT};
}}

QTreeWidget::item {{
    padding: 4px 2px;
    border: none;
}}

QTreeWidget::item:selected {{
    background-color: {COLOR_BG_HIGHLIGHT};
}}

QTreeWidget::item:hover {{
    background-color: {COLOR_BG_TREE_HOVER};
}}

QHeaderView::section {{
    background-color: {COLOR_BG_HEADER};
    color: {COLOR_TEXT_PRIMARY};
    padding: 4px;
    border: 1px solid {COLOR_BORDER};
}}

QFrame[frameShape="4"] {{
    /* HLine */
    background-color: {COLOR_BORDER};
    max-height: 1px;
}}

QScrollBar:vertical {{
    background-color: {COLOR_SCROLLBAR_BG};
    width: 12px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {COLOR_SCROLLBAR_HANDLE};
    border-radius: 4px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLOR_SCROLLBAR_HANDLE_HOVER};
}}

QToolTip {{
    background-color: {COLOR_BG_TOOLTIP};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    padding: 4px;
}}

QSplitter::handle {{
    background-color: {COLOR_BORDER};
}}

QSplitter::handle:hover {{
    background-color: {COLOR_ACCENT};
}}

QTabWidget::pane {{
    border: 1px solid {COLOR_BORDER};
    background-color: {COLOR_BG_PRIMARY};
}}

QTabBar::tab {{
    background-color: {COLOR_BG_TAB};
    color: {COLOR_TEXT_PRIMARY};
    padding: 8px 16px;
    border: 1px solid {COLOR_BORDER};
    border-bottom: none;
}}

QTabBar::tab:selected {{
    background-color: {COLOR_BG_PRIMARY};
    border-bottom: 2px solid {COLOR_ACCENT};
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLOR_BG_BUTTON};
}}
"""

# Create the stylesheet constant
DARK_STYLESHEET: str = _create_dark_stylesheet()
