# Shadow Army - Iniciar Panel (Windows)
#   .\scripts\iniciar_panel_win.ps1
#   .\scripts\iniciar_panel_win.ps1 -SoloPanel
#   .\scripts\iniciar_panel_win.ps1 -Puerto 8765
#
# Nota: "Iniciar Panel.command" es de macOS - en Windows usa este .ps1
param(
    [int]$Puerto = 8080,
    [switch]$SoloPanel
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$LogDir = Join-Path $Root "data\logs"
New-Item -ItemType Directory -Force -Path $LogDir, (Join-Path $Root "data") | Out-Null

function Stop-NamedPython {
    param([string]$Pattern)
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "python" -and $_.CommandLine -match $Pattern } |
        ForEach-Object {
            try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
        }
}

function Liberar-Puerto {
    param([int]$Port)
    Stop-NamedPython "http.server\s+$Port"
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object {
            try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
        }
    Start-Sleep -Milliseconds 400
}

Write-Host ""
Write-Host "=== Shadow Army - Panel (Windows) ===" -ForegroundColor Cyan
Write-Host ("Carpeta: {0}" -f $Root)
Write-Host ("Puerto:  {0}" -f $Puerto)
Write-Host ""

if (Test-Path "$Root\.venv\Scripts\python.exe") {
    $Py = "$Root\.venv\Scripts\python.exe"
} else {
    $Py = "python"
}

Liberar-Puerto -Port $Puerto

$ArisePid = $null
if (-not $SoloPanel) {
    Write-Host "Arrancando arise.py ..."
    Stop-NamedPython "arise\.py"
    $ariseOut = Join-Path $LogDir "arise_panel_out.log"
    $ariseErr = Join-Path $LogDir "arise_panel_err.log"
    $ariseProc = Start-Process -FilePath $Py -ArgumentList "arise.py" `
        -WorkingDirectory $Root -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $ariseOut -RedirectStandardError $ariseErr
    $ArisePid = $ariseProc.Id
    Set-Content -Path (Join-Path $Root "data\panel_arise.pid") -Value $ArisePid
    Start-Sleep -Seconds 2
    Write-Host ("  arise PID {0}" -f $ArisePid)
} else {
    Write-Host "Solo Pergamino (sin arise)"
}

Write-Host "Servidor http ..."
$httpOut = Join-Path $LogDir "panel_http_out.log"
$httpErr = Join-Path $LogDir "panel_http_err.log"
$httpProc = Start-Process -FilePath $Py -ArgumentList "-m","http.server","$Puerto","--directory",$Root `
    -WorkingDirectory $Root -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $httpOut -RedirectStandardError $httpErr
Set-Content -Path (Join-Path $Root "data\panel_http.pid") -Value $httpProc.Id
Start-Sleep -Seconds 1

$bust = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$url = "http://localhost:${Puerto}/dashboard_sombras.html?v=$bust"
Start-Process $url

Write-Host ""
Write-Host "Panel listo." -ForegroundColor Green
Write-Host ("  Pergamino (PC): {0}" -f $url)
try {
    $lan = (Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -notmatch '^127\.' -and $_.IPAddress -notmatch '^169\.' } |
        Select-Object -First 1 -ExpandProperty IPAddress)
    if ($lan) {
        Write-Host ("  Pergamino (telefono misma WiFi): http://{0}:{1}/dashboard_sombras.html" -f $lan, $Puerto) -ForegroundColor Cyan
    }
} catch {}
Write-Host ("  http.server PID {0}" -f $httpProc.Id)
if ($ArisePid) { Write-Host ("  arise.py PID {0}" -f $ArisePid) }
Write-Host "  Detener: .\scripts\detener_panel_win.ps1"
Write-Host ""
