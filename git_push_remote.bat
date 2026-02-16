@echo off
REM Push code changes to remote WITHOUT files listed in .gitignore-remote
REM Usage: git_push_remote.bat "Your commit message"

setlocal enabledelayedexpansion

if "%~1"=="" (
    echo Error: Commit message required
    echo Usage: git_push_remote.bat "Your commit message"
    exit /b 1
)

set "COMMIT_MSG=%~1"
set "EXCLUDE_FILE=.gitignore-remote"

echo.
echo ========================================
echo  Pushing code to remote (excluding personal files)
echo ========================================
echo.

REM Check if exclude file exists
if not exist "%EXCLUDE_FILE%" (
    echo ERROR: %EXCLUDE_FILE% not found
    echo Create this file with patterns to exclude from remote
    exit /b 1
)

REM Switch to main branch
echo [1/6] Switching to main branch...
git checkout main
if errorlevel 1 (
    echo ERROR: Could not switch to main branch
    exit /b 1
)

REM Merge from local but don't commit
echo [2/6] Merging changes from local branch...
git merge local --no-commit --no-ff
if errorlevel 1 (
    echo.
    echo ERROR: Merge conflict detected!
    echo Please resolve conflicts manually:
    echo   1. Fix conflicts in the files
    echo   2. git add [resolved files]
    echo   3. git commit -m "%COMMIT_MSG%"
    echo   4. git push origin main
    echo   5. git checkout local
    exit /b 1
)

REM Unstage and restore files from .gitignore-remote
echo [3/6] Excluding files from remote (reading %EXCLUDE_FILE%)...
set EXCLUDE_COUNT=0
for /f "usebackq eol=# tokens=*" %%F in ("%EXCLUDE_FILE%") do (
    set "line=%%F"
    REM Skip empty lines
    if not "!line!"=="" (
        REM Check if it's a simple file path (not a pattern with wildcards)
        echo !line! | findstr /C:"*" >nul
        if errorlevel 1 (
            REM No wildcard - unstage and restore specific file
            git reset HEAD "%%F" 2>nul
            git checkout -- "%%F" 2>nul
            if not errorlevel 1 set /a EXCLUDE_COUNT+=1
        ) else (
            REM Has wildcard - use git ls-files to expand
            for /f "delims=" %%G in ('git ls-files "%%F" 2^>nul') do (
                git reset HEAD "%%G" 2>nul
                git checkout -- "%%G" 2>nul
                if not errorlevel 1 set /a EXCLUDE_COUNT+=1
            )
        )
    )
)
echo Excluded %EXCLUDE_COUNT% file(s) from remote push

REM Check if there are any changes to commit
echo [4/6] Checking for changes...
git diff --cached --quiet
if errorlevel 1 (
    echo Changes found - proceeding with commit
) else (
    echo.
    echo WARNING: No code changes to push
    echo Aborting merge and returning to local branch
    git merge --abort 2>nul
    git checkout local
    exit /b 0
)

REM Show what will be pushed
echo.
echo Files being pushed:
git diff --cached --name-only

REM Commit
echo.
echo [5/6] Committing changes...
git commit -m "%COMMIT_MSG%"
if errorlevel 1 (
    echo ERROR: Commit failed
    git checkout local
    exit /b 1
)

REM Push to remote
echo [6/6] Pushing to origin/main...
git push origin main
if errorlevel 1 (
    echo ERROR: Push failed
    echo You may need to pull first: git pull origin main
    git checkout local
    exit /b 1
)

echo.
echo ========================================
echo  SUCCESS: Pushed to remote
echo ========================================
echo  Branch: main -^> origin/main
echo  Message: %COMMIT_MSG%
echo  Excluded: See %EXCLUDE_FILE%
echo ========================================
echo.

REM Return to local branch
echo Returning to local branch...
git checkout local

echo.
echo Done! You're back on the local branch.
