@echo off
REM Preview what would be pushed to remote WITHOUT actually pushing
REM Shows files that will go to remote after .gitignore-remote filtering

setlocal enabledelayedexpansion

set "EXCLUDE_FILE=.gitignore-remote"

echo.
echo ========================================
echo  Push Preview (Dry Run)
echo ========================================
echo.

REM Check if exclude file exists
if not exist "%EXCLUDE_FILE%" (
    echo ERROR: %EXCLUDE_FILE% not found
    exit /b 1
)

REM Get current branch
for /f %%i in ('git rev-parse --abbrev-ref HEAD') do set CURRENT_BRANCH=%%i
echo Current branch: %CURRENT_BRANCH%
echo.

REM Switch to main branch
echo [1/5] Switching to main branch...
git checkout main >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not switch to main branch
    exit /b 1
)

REM Merge from local but don't commit
echo [2/5] Merging changes from local branch...
git merge local --no-commit --no-ff >nul 2>&1
if errorlevel 1 (
    echo ERROR: Merge conflict detected - aborting preview
    git merge --abort >nul 2>&1
    git checkout %CURRENT_BRANCH% >nul 2>&1
    exit /b 1
)

REM Unstage and restore files from .gitignore-remote
echo [3/5] Applying .gitignore-remote exclusions...
set EXCLUDE_COUNT=0
for /f "usebackq eol=# tokens=*" %%F in ("%EXCLUDE_FILE%") do (
    set "line=%%F"
    if not "!line!"=="" (
        echo !line! | findstr /C:"*" >nul
        if errorlevel 1 (
            git reset HEAD "%%F" >nul 2>&1
            git checkout -- "%%F" >nul 2>&1
            if not errorlevel 1 set /a EXCLUDE_COUNT+=1
        ) else (
            for /f "delims=" %%G in ('git ls-files "%%F" 2^>nul') do (
                git reset HEAD "%%G" >nul 2>&1
                git checkout -- "%%G" >nul 2>&1
                if not errorlevel 1 set /a EXCLUDE_COUNT+=1
            )
        )
    )
)
echo Excluded %EXCLUDE_COUNT% file(s) from push

REM Check if there are any changes
echo [4/5] Checking what would be pushed...
git diff --cached --quiet
if not errorlevel 1 (
    echo.
    echo ========================================
    echo  NO CHANGES TO PUSH
    echo ========================================
    git merge --abort >nul 2>&1
    git checkout %CURRENT_BRANCH% >nul 2>&1
    exit /b 0
)

REM Show what would be pushed
echo [5/5] Generating file list...
echo.
echo ========================================
echo  FILES THAT WOULD BE PUSHED:
echo ========================================
git diff --cached --name-only

echo.
echo ========================================
echo  STATISTICS:
echo ========================================
for /f %%i in ('git diff --cached --name-only ^| find /c /v ""') do echo Total files: %%i

REM Show file counts by folder
echo.
echo Files by folder:
for /f "tokens=1 delims=/" %%d in ('git diff --cached --name-only') do echo   %%d\...

REM Cleanup - abort merge and return to original branch
echo.
echo ========================================
echo  PREVIEW COMPLETE - NO CHANGES MADE
echo ========================================
git merge --abort >nul 2>&1
git checkout %CURRENT_BRANCH% >nul 2>&1

echo.
echo Returned to %CURRENT_BRANCH% branch
echo.
