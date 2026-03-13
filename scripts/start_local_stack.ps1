param(
    [ValidateSet("docker", "dev")]
    [string]$Mode = "docker"
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> project root: $Root"

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "==> created .env from .env.example"
}

if ($Mode -eq "docker") {
    Write-Host "==> starting backend + frontend with docker compose"
    docker compose up --build
    exit $LASTEXITCODE
}

Write-Host "==> preparing local data directories"
python scripts\prepare_data_dirs.py

Write-Host "==> local dev mode"
Write-Host "   backend: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Write-Host "   frontend: cd frontend; npm run dev"
