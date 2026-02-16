@echo off
REM One-time setup for local/main branch workflow

echo.
echo ========================================
echo  LKS Git Workflow Setup
echo ========================================
echo.
echo This will set up a two-branch workflow:
echo   - local branch = all changes (code + configs)
echo   - main branch = code only (for remote)
echo.

REM Check if local branch exists
git rev-parse --verify local >nul 2>&1
if errorlevel 1 (
    echo Creating 'local' branch from current state...
    git checkout -b local
    if errorlevel 1 (
        echo ERROR: Failed to create local branch
        exit /b 1
    )
    
    echo Committing current configs to local branch...
    git add data/lks_*.json data/radial_menu_config.json 2>nul
    git commit -m "Initial config snapshot for local branch" 2>nul
    echo SUCCESS: Local branch created with configs tracked
) else (
    echo SUCCESS: Local branch already exists
)

echo.
echo Cleaning main branch (removing configs)...
git checkout main
if errorlevel 1 (
    echo ERROR: Failed to switch to main branch
    exit /b 1
)

REM Remove config files from main
set REMOVED=0
git rm --cached data/lks_ui_state.json 2>nul && set REMOVED=1
git rm --cached data/lks_panel_state.json 2>nul && set REMOVED=1
git rm --cached data/lks_settings.json 2>nul && set REMOVED=1
git rm --cached data/lks_autopo_settings.json 2>nul && set REMOVED=1
git rm --cached data/lks_brush_settings.json 2>nul && set REMOVED=1
git rm --cached data/radial_menu_config.json 2>nul && set REMOVED=1

if %REMOVED%==1 (
    git commit -m "Remove personal configs from main branch"
    echo SUCCESS: Configs removed from main branch
) else (
    echo SUCCESS: Main branch already clean (no configs tracked)
)

REM Return to local branch
git checkout local

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Daily workflow:
echo   1. Commit to 'local' branch (use VSCode UI)
echo   2. Push to remote: git_push_remote.bat "message"
echo   3. Edit exclusions: notepad .gitignore-remote
echo.
echo You're now on the 'local' branch - start working!
echo.
