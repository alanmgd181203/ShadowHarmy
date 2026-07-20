# Shadow Army — Panel con túnel HTTPS (PWA real en Android)
#
# Por qué: en Android, http://192.168.x.x NO instala app standalone.
# El icono solo abre Chrome CON barra URL. Hace falta HTTPS público (túnel).
#
# Uso:
#   .\scripts\iniciar_panel_pwa_win.ps1
#   .\scripts\iniciar_panel_pwa_win.ps1 -Puerto 8080
#
# Requisitos: cloudflared en PATH, o se descarga portable a tools\
#   https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
param(
    [int]$Puerto = 8080
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$LogDir = Join-Path $Root "data\logs"
$Tools = Join-Path $Root "tools"
New-Item -ItemType Directory -Force -Path $LogDir, $Tools | Out-Null

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
    Stop-NamedPython "panel_http_server"
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object {
            try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
        }
    Start-Sleep -Milliseconds 400
}

function Find-Cloudflared {
    $cmd = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $local = Join-Path $Tools "cloudflared.exe"
    if (Test-Path $local) { return $local }
    return $null
}

Write-Host ""
Write-Host "=== Shadow Army - Panel PWA (HTTPS tunel) ===" -ForegroundColor Cyan
Write-Host "Android necesita HTTPS real. HTTP LAN solo abre Chrome con barra URL."
Write-Host ""

if (Test-Path "$Root\.venv\Scripts\python.exe") {
    $Py = "$Root\.venv\Scripts\python.exe"
} else {
    $Py = "python"
}

$cf = Find-Cloudflared
if (-not $cf) {
    Write-Host "cloudflared no encontrado. Intentando descarga portable..." -ForegroundColor Yellow
    $url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    $dest = Join-Path $Tools "cloudflared.exe"
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
        $cf = $dest
        Write-Host ("  OK: {0}" -f $cf) -ForegroundColor Green
    } catch {
        Write-Host "No se pudo descargar cloudflared." -ForegroundColor Red
        Write-Host "Instala a mano: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
        Write-Host "O coloca cloudflared.exe en tools\ y vuelve a correr este script."
        exit 1
    }
}

Liberar-Puerto -Port $Puerto

Write-Host ("Servidor http local :{0} ..." -f $Puerto)
$httpOut = Join-Path $LogDir "panel_http_out.log"
$httpErr = Join-Path $LogDir "panel_http_err.log"
$httpProc = Start-Process -FilePath $Py -ArgumentList "scripts/panel_http_server.py","--port","$Puerto","--directory",$Root `
    -WorkingDirectory $Root -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $httpOut -RedirectStandardError $httpErr
Set-Content -Path (Join-Path $Root "data\panel_http.pid") -Value $httpProc.Id
Start-Sleep -Seconds 1

$tunnelLog = Join-Path $LogDir "cloudflared_pwa.log"
if (Test-Path $tunnelLog) { Remove-Item $tunnelLog -Force }
Write-Host "Abriendo tunel Cloudflare (HTTPS) ..."
$tunnelProc = Start-Process -FilePath $cf -ArgumentList "tunnel","--url","http://127.0.0.1:$Puerto" `
    -WorkingDirectory $Root -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $tunnelLog -RedirectStandardError $tunnelLog
Set-Content -Path (Join-Path $Root "data\panel_tunnel.pid") -Value $tunnelProc.Id

$httpsUrl = $null
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    if (-not (Test-Path $tunnelLog)) { continue }
    $txt = Get-Content $tunnelLog -Raw -ErrorAction SilentlyContinue
    if ($txt -match 'https://[a-zA-Z0-9.-]+\.trycloudflare\.com') {
        $httpsUrl = $Matches[0]
        break
    }
}

Write-Host ""
if ($httpsUrl) {
    $dash = "$httpsUrl/dashboard_sombras.html"
    Write-Host "LISTO — usa ESTA URL en el celular (no la IP http):" -ForegroundColor Green
    Write-Host ("  {0}" -f $dash) -ForegroundColor Cyan
    Write-Host ""
    Write-Host "En Android Chrome:"
    Write-Host "  1) Abre la URL https de arriba"
    Write-Host "  2) Menu ⋮ → Instalar app (o Añadir a pantalla de inicio)"
    Write-Host "  3) Borra el icono VIEJO (el de la IP http)"
    Write-Host "  4) Abre el icono NUEVO — ahi sí sin barra URL"
    Write-Host ""
    try { Set-Clipboard -Value $dash } catch {}
    Write-Host "(URL copiada al portapapeles si se pudo)"
} else {
    Write-Host "Tunel arranco pero no lei la URL a tiempo." -ForegroundColor Yellow
    Write-Host ("Revisa el log: {0}" -f $tunnelLog)
}

Write-Host ("  panel_http PID {0}" -f $httpProc.Id)
Write-Host ("  cloudflared PID {0}" -f $tunnelProc.Id)
Write-Host "  Detener: .\scripts\detener_panel_win.ps1"
Write-Host ""
