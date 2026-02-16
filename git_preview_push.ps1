#!/usr/bin/env pwsh
# Preview what would be pushed to remote WITHOUT actually pushing

param(
    [switch]$Detailed  # Show detailed diff stats
)

$excludeFile = ".gitignore-remote"

# Check if exclude file exists
if (-not (Test-Path $excludeFile)) {
    Write-Host "✗ Error: $excludeFile not found" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Push Preview (Dry Run)" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Get current branch
$currentBranch = git rev-parse --abbrev-ref HEAD
Write-Host "Current branch: $currentBranch" -ForegroundColor Gray

# Switch to main branch
Write-Host "`n[1/5] Switching to main branch..." -ForegroundColor Yellow
git checkout main 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error: Could not switch to main branch" -ForegroundColor Red
    exit 1
}

# Merge from local but don't commit
Write-Host "[2/5] Merging changes from local branch..." -ForegroundColor Yellow
git merge local --no-commit --no-ff 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error: Merge conflict detected - aborting preview" -ForegroundColor Red
    git merge --abort 2>$null
    git checkout $currentBranch 2>$null
    exit 1
}

# Read exclude patterns
$excludePatterns = Get-Content $excludeFile | Where-Object { 
    $_ -notmatch '^\s*#' -and $_ -notmatch '^\s*$' 
}

# Unstage and restore files matching exclude patterns
Write-Host "[3/5] Applying .gitignore-remote exclusions..." -ForegroundColor Yellow
$excludeCount = 0
foreach ($pattern in $excludePatterns) {
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
Write-Host "Excluded $excludeCount file(s) from push" -ForegroundColor Gray

# Check if there are any changes
Write-Host "[4/5] Checking what would be pushed..." -ForegroundColor Yellow
$changes = git diff --cached --name-only
if ([string]::IsNullOrWhiteSpace($changes)) {
    Write-Host "`n========================================" -ForegroundColor Yellow
    Write-Host "  NO CHANGES TO PUSH" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    git merge --abort 2>$null
    git checkout $currentBranch 2>$null
    exit 0
}

# Show what would be pushed
Write-Host "[5/5] Generating file list...`n" -ForegroundColor Yellow

Write-Host "========================================" -ForegroundColor Green
Write-Host "  FILES THAT WOULD BE PUSHED:" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
$files = git diff --cached --name-only
$files | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  STATISTICS:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total files: $($files.Count)" -ForegroundColor White

# Group by folder
$byFolder = $files | Group-Object { $_.Split('/')[0] } | Sort-Object Count -Descending
Write-Host "`nFiles by folder:" -ForegroundColor White
foreach ($group in $byFolder) {
    Write-Host "  $($group.Name)/: $($group.Count) files" -ForegroundColor Gray
}

# Show detailed stats if requested
if ($Detailed) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  DETAILED DIFF STATS:" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    git diff --cached --stat
}

# Cleanup
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  PREVIEW COMPLETE - NO CHANGES MADE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
git merge --abort 2>$null
git checkout $currentBranch 2>$null

Write-Host "`nReturned to $currentBranch branch" -ForegroundColor Gray
Write-Host ""
