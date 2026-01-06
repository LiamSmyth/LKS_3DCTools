@echo off
REM Package LKS cModule for distribution
REM Double-click to create a release zip, or run with arguments:
REM   package_release.bat --version 1.0.0
REM   package_release.bat --dry-run

cd /d "%~dp0"
python package_release.py %*
pause
