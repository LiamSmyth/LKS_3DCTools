"""
LKS cModule startup initialization.

This file is executed when 3DCoat starts and the LKS cModule is loaded.
It initializes Qt/PySide6 for non-blocking UI panels.
"""
import sys

# Configure Qt for 3DCoat compatibility BEFORE importing QApplication
try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
    
    # CRITICAL: Use desktop OpenGL to avoid conflicts with 3DCoat's rendering
    QApplication.setAttribute(Qt.AA_UseDesktopOpenGL)
    
    # Create QApplication with no-opengl flag if not already created
    if not QApplication.instance():
        app = QApplication(["-no-opengl"])
        print("[LKS] Qt initialized successfully")
    else:
        print("[LKS] Qt already initialized")
        
except ImportError as e:
    print(f"[LKS] Warning: PySide6 not available: {e}")
    print("[LKS] Qt UI features will be disabled")
except Exception as e:
    print(f"[LKS] Error initializing Qt: {e}")
