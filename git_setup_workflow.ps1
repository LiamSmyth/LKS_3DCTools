#!/usr/bin/env pwsh
# One-time setup for local/main branch workflow

Write-Host "=== LKS Git Workflow Setup ===" -ForegroundColor Cyan
Write-Host "This will set up a two-branch workflow:" -ForegroundColor White
Write-Host "  • local branch = all your changes (code + configs)" -ForegroundColor Gray
Write-Host "  • main branch = code only (for remote push)" -ForegroundColor Gray
Write-Host ""

$currentBranch = git rev-parse --abbrev-ref HEAD

# Check if local branch already exists
$localExists = git rev-parse --verify local 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Local branch already exists" -ForegroundColor Green
    $createLocal = $false
} else {
    Write-Host "Creating 'local' branch from current state..." -ForegroundColor Yellow
    git checkout -b local
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to create local branch" -ForegroundColor Red
        exit 1
    }
    
    # Commit current configs on local branch
    Write-Host "Committing current configs to local branch..." -ForegroundColor Yellow
    git add data/lks_*.json data/radial_menu_config.json 2>$null
    git commit -m "Initial config snapshot for local branch" 2>$null
    Write-Host "✓ Local branch created with configs tracked" -ForegroundColor Green
    $createLocal = $true
}

# Switch to main and remove configs
Write-Host "`nCleaning main branch (removing configs)..." -ForegroundColor Yellow
git checkout main
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to switch to main branch" -ForegroundColor Red
    exit 1
}

$configFiles = @(
    "data/lks_ui_state.json",
    "data/lks_panel_state.json",
    "data/lks_settings.json",
    "data/lks_autopo_settings.json",
    "data/lks_brush_settings.json",
    "data/radial_menu_config.json"
)

$removedAny = $false
foreach ($file in $configFiles) {
    if (Test-Path $file) {
        git rm --cached $file 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Untracked: $file" -ForegroundColor Gray
            $removedAny = $true
        }
    }
}

if ($removedAny) {
    git commit -m "Remove personal configs from main branch"
    Write-Host "✓ Configs removed from main branch" -ForegroundColor Green
} else {
    Write-Host "✓ Main branch already clean (no configs tracked)" -ForegroundColor Green
}

# Return to local branch
git checkout local

Write-Host "`n=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Daily workflow:" -ForegroundColor Cyan
Write-Host "  1. Work and commit configs locally:" -ForegroundColor White
Write-Host "     .\git_commit_local.ps1 `"Your commit message`"" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. Push code to remote (excludes files in .gitignore-remote):" -ForegroundColor White
Write-Host "     .\git_push_remote.ps1 `"Your commit message`"" -ForegroundColor Yellow
Write-Host ""
Write-Host "You're now on the 'local' branch - start working!" -ForegroundColor Green
