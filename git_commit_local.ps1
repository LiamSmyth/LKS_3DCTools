#!/usr/bin/env pwsh
# Save all changes (code + configs) to local branch

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Message
)

# Ensure we're on local branch
$currentBranch = git rev-parse --abbrev-ref HEAD

if ($currentBranch -ne "local") {
    Write-Host "Switching to local branch..." -ForegroundColor Yellow
    git checkout local
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Could not switch to local branch. Create it first with:" -ForegroundColor Red
        Write-Host "  git checkout -b local" -ForegroundColor Red
        exit 1
    }
}

# Add and commit everything
git add .
git commit -m $Message

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Committed to local branch (configs saved in history)" -ForegroundColor Green
    Write-Host "  Branch: local" -ForegroundColor Gray
    Write-Host "  Message: $Message" -ForegroundColor Gray
}
else {
    Write-Host "✗ Commit failed or nothing to commit" -ForegroundColor Red
}
