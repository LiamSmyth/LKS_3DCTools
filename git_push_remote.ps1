#!/usr/bin/env pwsh
# Push code changes to remote WITHOUT files listed in .gitignore-remote

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Message
)

$excludeFile = ".gitignore-remote"

# Check if exclude file exists
if (-not (Test-Path $excludeFile)) {
    Write-Host "[X] Error: $excludeFile not found" -ForegroundColor Red
    Write-Host "Create this file with patterns to exclude from remote" -ForegroundColor Yellow
    exit 1
}

Write-Host "Preparing to push code-only changes to remote..." -ForegroundColor Cyan
Write-Host "Exclude rules: $excludeFile" -ForegroundColor Gray

# Read exclude patterns from file
$excludePatterns = Get-Content $excludeFile | Where-Object { 
    $_ -notmatch '^\s*#' -and $_ -notmatch '^\s*$' 
}

# Switch to main branch
git checkout main
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Error: Could not switch to main branch" -ForegroundColor Red
    exit 1
}

# Merge from local but don't commit
Write-Host "Merging from local branch..." -ForegroundColor Yellow
git merge local --no-commit --no-ff
$mergeResult = $LASTEXITCODE

if ($mergeResult -ne 0) {
    Write-Host "[X] Merge conflict! Resolve conflicts then run:" -ForegroundColor Red
    Write-Host "  git commit -m `"$Message`"" -ForegroundColor Yellow
    Write-Host "  git push origin main" -ForegroundColor Yellow
    Write-Host "  git checkout local" -ForegroundColor Yellow
    exit 1
}

# Unstage and restore files matching exclude patterns
Write-Host "Excluding files from remote (reading $excludeFile)..." -ForegroundColor Yellow
$excludeCount = 0
foreach ($pattern in $excludePatterns) {
    # Get files matching the pattern
    $matchingFiles = git ls-files $pattern 2>$null
    if ($matchingFiles) {
        foreach ($file in $matchingFiles) {
            git reset HEAD $file 2>$null
            git checkout -- $file 2>$null
            if ($LASTEXITCODE -eq 0) {
                $excludeCount++
            }
        }
    }
}
Write-Host "Excluded $excludeCount file(s) from remote push" -ForegroundColor Gray

# Check if there are any changes to commit
$changes = git diff --cached --name-only
if ([string]::IsNullOrWhiteSpace($changes)) {
    Write-Host "`n[!] No code changes to push" -ForegroundColor Yellow
    git merge --abort 2>$null
    git checkout local
    exit 0
}

# Show what will be pushed
Write-Host "`nFiles being pushed:" -ForegroundColor Cyan
git diff --cached --name-only | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }

# Commit and push
git commit -m $Message
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[OK] Pushed to remote" -ForegroundColor Green
    Write-Host "  Branch: main -> origin/main" -ForegroundColor Gray
    Write-Host "  Message: $Message" -ForegroundColor Gray
    Write-Host "  Excluded: See $excludeFile" -ForegroundColor Gray
} else {
    Write-Host "`n[X] Push failed" -ForegroundColor Red
}

# Return to local branch
Write-Host "`nReturning to local branch..." -ForegroundColor Yellow
git checkout local
