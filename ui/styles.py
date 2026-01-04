"""
LKS UI Styles.

Contains Qt stylesheets and theme definitions for the LKS panel.
Separated from main code for maintainability.
"""

# =============================================================================
# DARK THEME STYLESHEET
# =============================================================================

DARK_STYLESHEET: str = """
QWidget {
    background-color: #2b2b2b;
    color: #e0e0e0;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 11px;
}

QGroupBox {
    border: 1px solid #555555;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    color: #90caf9;
}

QPushButton {
    background-color: #404040;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 12px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #4a4a4a;
    border-color: #90caf9;
}

QPushButton:pressed {
    background-color: #353535;
}

QPushButton:disabled {
    background-color: #333333;
    color: #666666;
}

QLabel {
    background-color: transparent;
}

QTreeWidget {
    background-color: #1e1e1e;
    border: 1px solid #555555;
    border-radius: 4px;
    alternate-background-color: #252525;
}

QTreeWidget::item {
    padding: 4px 2px;
    border: none;
}

QTreeWidget::item:selected {
    background-color: #264f78;
}

QTreeWidget::item:hover {
    background-color: #3a3a3a;
}

QHeaderView::section {
    background-color: #383838;
    color: #e0e0e0;
    padding: 4px;
    border: 1px solid #555555;
}

QFrame[frameShape="4"] {
    /* HLine */
    background-color: #555555;
    max-height: 1px;
}

QScrollBar:vertical {
    background-color: #2b2b2b;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #555555;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #666666;
}

QToolTip {
    background-color: #3c3c3c;
    color: #e0e0e0;
    border: 1px solid #555555;
    padding: 4px;
}

QSplitter::handle {
    background-color: #555555;
}

QSplitter::handle:hover {
    background-color: #90caf9;
}

QTabWidget::pane {
    border: 1px solid #555555;
    background-color: #2b2b2b;
}

QTabBar::tab {
    background-color: #353535;
    color: #e0e0e0;
    padding: 8px 16px;
    border: 1px solid #555555;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #2b2b2b;
    border-bottom: 2px solid #90caf9;
}

QTabBar::tab:hover:!selected {
    background-color: #404040;
}
"""

# =============================================================================
# COLOR CONSTANTS (for programmatic use)
# =============================================================================

COLOR_BG_PRIMARY: str = "#2b2b2b"
COLOR_BG_SECONDARY: str = "#1e1e1e"
COLOR_BG_HIGHLIGHT: str = "#264f78"
COLOR_TEXT_PRIMARY: str = "#e0e0e0"
COLOR_TEXT_MUTED: str = "#888888"
COLOR_ACCENT: str = "#90caf9"
COLOR_SUCCESS: str = "#81c784"
COLOR_WARNING: str = "#ffb74d"
COLOR_ERROR: str = "#ef5350"
COLOR_BORDER: str = "#555555"
