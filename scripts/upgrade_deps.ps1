<#
.SYNOPSIS
    Automated helper to upgrade Python dependencies to their latest stable releases

.DESCRIPTION
    This script creates a git branch, sets up a virtual environment, uses
    pip-tools to resolve and pin the latest stable versions of top-level
    dependencies and runs basic checks (migrations, tests, Docker build).

.NOTES
    Run from the repository root on Windows PowerShell. Review the generated
    changes before committing. This script performs network operations.

    Usage:
      .\scripts\upgrade_deps.ps1 [-AutoConfirm]

#>

param(
    [switch]$AutoConfirm
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Prompt-Continue {
    param([string]$msg)
    if ($AutoConfirm) { return $true }
    Write-Host $msg -ForegroundColor Yellow
    $r = Read-Host "Continue? (y/n)"
    return $r -match '^[Yy]'
}

Write-Host "Starting dependency upgrade workflow" -ForegroundColor Cyan

# 1) create branch
$branch = 'upgrade/deps-latest'
Write-Host "Creating branch: $branch" -ForegroundColor Green
git checkout -b $branch

# 2) create venv and activate
if (-Not (Test-Path -Path .venv)) {
    Write-Host "Creating virtualenv .venv" -ForegroundColor Green
    python -m venv .venv
}
Write-Host "Activating virtualenv" -ForegroundColor Green
. .\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip/setuptools/wheel and installing pip-tools" -ForegroundColor Green
python -m pip install --upgrade pip setuptools wheel
pip install --upgrade pip-tools

# 3) prepare requirements.in if missing
if (-Not (Test-Path requirements.in)) {
    Write-Host "Generating requirements.in from requirements.txt" -ForegroundColor Green
    $lines = Get-Content requirements.txt | ForEach-Object { $_.Trim() } | Where-Object { $_ -and -not ($_ -like '#*') }
    $pkgs = @()
    foreach ($l in $lines) {
        # remove extras and version specifiers
        $n = $l -replace '\s*#.*$', ''
        $n = $n -replace '\s*\[.*?\]', ''
        # split on comparison operators
        $n = $n -split '(==|>=|<=|~=|!=|>|<)'
        if ($n.Length -gt 0) { $pkg = $n[0].Trim(); if ($pkg) { $pkgs += $pkg } }
    }
    $pkgs | Sort-Object -Unique | Set-Content requirements.in
    Write-Host "Wrote `requirements.in` with top-level packages." -ForegroundColor Green
}

if (-Not (Prompt-Continue "About to run pip-compile --upgrade which will rewrite requirements.txt.")) { Write-Host "Aborted"; exit 1 }

# 4) run pip-compile to pin latest stable versions
Write-Host "Running pip-compile --upgrade" -ForegroundColor Green
pip-compile --upgrade --output-file=requirements.txt requirements.in

# 5) install and run basic checks
Write-Host "Installing pinned requirements" -ForegroundColor Green
pip install -r requirements.txt

Write-Host "Running migrations" -ForegroundColor Green
python manage.py migrate --noinput

if (Test-Path pytest.ini -or (Get-Command pytest -ErrorAction SilentlyContinue)) {
    Write-Host "Running pytest (if available)" -ForegroundColor Green
    try { pytest -q } catch { Write-Host "pytest failed or not configured: $_" -ForegroundColor Yellow }
} else {
    Write-Host "Running Django tests via manage.py test" -ForegroundColor Green
    try { python manage.py test } catch { Write-Host "Django tests failed or not configured: $_" -ForegroundColor Yellow }
}

if (-Not (Prompt-Continue "Attempt Docker build locally to validate image? This may take several minutes.")) { Write-Host "Skipping Docker build"; exit 0 }

Write-Host "Building Docker image: aulamax:upgrade-test" -ForegroundColor Green
docker build -t aulamax:upgrade-test .

Write-Host "Upgrade script finished. Review changes, run the app and tests manually as needed." -ForegroundColor Cyan
