# Shadow Army — Detener Panel (Windows)
#   .\scripts\detener_panel_win.ps1
param(
    [int]$Puerto = 8080
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Stop-NamedPython {
    param([string]$Pattern)
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "python" -and $_.CommandLine -match $Pattern } |
        ForEach-Object {
            try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
        }
}

Write-Host "Deteniendo panel..." -ForegroundColor Yellow

foreach ($name in @("panel_arise.pid", "panel_http.pid", "panel_tunnel.pid")) {
    $path = Join-Path $Root "data\$name"
    if (Test-Path $path) {
        $pidVal = (Get-Content $path -ErrorAction SilentlyContinue | Select-Object -First 1)
        if ($pidVal) {
            try { Stop-Process -Id ([int]$pidVal) -Force -ErrorAction SilentlyContinue } catch {}
        }
        Remove-Item $path -Force -ErrorAction SilentlyContinue
    }
}

Stop-NamedPython "arise\.py"
Stop-NamedPython "http.server\s+$Puerto"
Stop-NamedPython "panel_http_server"

Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match "cloudflared" -and $_.CommandLine -match "tunnel" } |
    ForEach-Object {
        try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
    }

Get-NetTCPConnection -LocalPort $Puerto -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object {
        try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
    }

Write-Host "Panel detenido." -ForegroundColor Green
