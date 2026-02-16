# Git Workflow: Local Config Tracking Without Remote Push

## Overview

This repository uses a **two-branch workflow** with an **external exclusion file** (`.gitignore-remote`) to maintain personal configs in git history locally without pushing them to remote:

- **`local` branch**: Full history including UI state, prefs - committed here  
- **`main` branch**: Code-only branch for remote - files from `.gitignore-remote` never merged here
- **`.gitignore-remote`**: List of files/patterns excluded from remote (gitignore format)

## Quick Reference

```powershell
# Daily work - commit everything including configs
git checkout local
git add .
git commit -m "Update features and UI layout"

# Push code to remote (files in .gitignore-remote stay on local branch)
.\git_push_remote.ps1 "Update features"
```

## Managing Exclusions

Edit `.gitignore-remote` to control what gets excluded from remote:

```bash
# Example .gitignore-remote content
data/lks_ui_state.json
data/lks_panel_state.json
data/*.log
dist/
```

Supports gitignore patterns: `*`, `?`, `**`, etc.

## Initial Setup (One Time)

### 1. Create the Local Branch

```powershell
# Run the setup script
.\git_setup_workflow.ps1
# OR .\git_setup_workflow.bat

# This creates 'local' branch from current state
# Commits all configs (tracked in history!)
# Cleans 'main' branch (removes configs)
```

### 2. Use Helper Scripts

**`git_commit_local.ps1`** (Save configs locally):
```powershell
.\git_commit_local.ps1 "Add feature and tweak UI"
```

**`git_push_remote.ps1`** (Push code without files from .gitignore-remote):
```powershell
.\git_push_remote.ps1 "Add feature"
```

**`PUSH_TO_REMOTE.bat`** (Double-click, prompts for message)

## Daily Workflow

### Option A: Using Helper Scripts

```powershell
# Work on code, modify configs, save everything locally
./git_commit_local.ps1 "Add new feature and tweak UI"

# Push only code to remote
./git_push_remote.ps1 "Add new feature"
```

### Option B: Using VSCode + Batch Script

1. Commit normally in VSCode (stays on `local` branch)
2. Double-click `PUSH_TO_REMOTE.bat` when ready to push
3. Enter commit message

### Option C: Manual Commands

```powershell
# 1. Work on local branch (commit everything)
git checkout local
# ... make changes to code and configs ...
git add .
git commit -m "Add feature X, adjust panel layout"

# 2. When ready to push code (not configs)
git checkout main

# 3. Merge but don't commit yet
git merge local --no-commit --no-ff

# 4. Unstage files from .gitignore-remote (script does this automatically)

# 5. Commit and push
git commit -m "Add feature X"
git push origin main

# 6. Back to work
git checkout local
```

## What's Tracked Where

### Local Branch (Full History)
- ✅ All code changes
- ✅ Files in `.gitignore-remote` (UI state, settings, etc.)
- ✅ Full history of config changes
- ✅ Docs and experiments

### Main Branch (Remote)
- ✅ All code changes
- ✅ Schemas (`*_schema.json`)
- ❌ No files matching patterns in `.gitignore-remote`
- ❌ No debug logs

## Customizing Exclusions

Edit `.gitignore-remote` to add/remove exclusions:

```powershell
notepad .gitignore-remote
```

Changes take effect immediately on next push.

## Checking Status

```powershell
# See what's different between branches
git diff main..local --name-only

# See which configs are on local only
git diff main..local -- data/

# Verify main doesn't have configs
git checkout main
git ls-files data/lks_*.json  # Should show nothing

# Test what will be excluded on next push
Get-Content .gitignore-remote | Where-Object { $_ -notmatch '^#' }
```

## Tips

1. **Always work on `local` branch** - This is your daily driver
2. **Main is just for pushing** - Think of it as a "clean export"
3. **Edit .gitignore-remote** - to change what gets excluded
4. **Config changes** - Commit them freely on local, they'll never reach remote
5. **Pattern matching** - `.gitignore-remote` supports wildcards like `*.log`, `data/*`

## Troubleshooting

### "I accidentally committed configs on main"
```powershell
git checkout main
git rm --cached data/lks_ui_state.json  # (and other configs)
git commit -m "Remove configs from main"
```

### "I want to see config history"
```powershell
git checkout local
git log --follow data/lks_ui_state.json
```

### "I want to add more files to exclusion list"
```powershell
# Edit .gitignore-remote
notepad .gitignore-remote
# Add patterns, one per line
```

### "A new file needs to be excluded"
```powershell
# Add to .gitignore-remote
echo data/new_personal_file.json >> .gitignore-remote
# Next push will automatically exclude it
```