# Shadow Army — Cascada React en el celular (PWA + tunel HTTPS)
# NO despierta ni mata Beru / Igris / arise.
#
# Uso:
#   .\scripts\iniciar_panel_pwa_win.ps1
#   .\scripts\iniciar_panel_pwa_win.ps1 -Puerto 5173
#
# Requisitos: Node/npm + cloudflared (se descarga portable a tools\ si falta)
param(
    [int]$Puerto = 5173
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Ui = Join-Path $Root "ui"
$LogDir = Join-Path $Root "data\logs"
$Tools = Join-Path $Root "tools"
New-Item -ItemType Directory -Force -Path $LogDir, $Tools, (Join-Path $Root "data") | Out-Null

function Find-Cloudflared {
    $cmd = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $local = Join-Path $Tools "cloudflared.exe"
    if (Test-Path $local) { return $local }
    return $null
}

function Liberar-Puerto {
    param([int]$Port)
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object {
            try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
        }
    Start-Sleep -Milliseconds 400
}

function Stop-PanelAnterior {
    foreach ($name in @("panel_http.pid", "panel_tunnel.pid", "panel_vite.pid", "panel_vite_tunnel.pid")) {
        $path = Join-Path $Root "data\$name"
        if (Test-Path $path) {
            $pidVal = (Get-Content $path -ErrorAction SilentlyContinue | Select-Object -First 1)
            if ($pidVal) {
                try { Stop-Process -Id ([int]$pidVal) -Force -ErrorAction SilentlyContinue } catch {}
            }
            Remove-Item $path -Force -ErrorAction SilentlyContinue
        }
    }
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            ($_.Name -match "cloudflared" -and $_.CommandLine -match "tunnel") -or
            ($_.CommandLine -match "panel_http_server") -or
            ($_.CommandLine -match "vite" -and $_.CommandLine -match "preview")
        } |
        ForEach-Object {
            try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
        }
}

Write-Host ""
Write-Host "=== Shadow Army - Cascada React (HTTPS tunel) ===" -ForegroundColor Cyan
Write-Host "No toca Beru ni Igris. Solo abre el Pergamino nuevo (flota rango)."
Write-Host ""

$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npm) {
    $nodeDirs = @(
        "C:\Program Files\nodejs",
        "${env:ProgramFiles}\nodejs",
        "${env:LOCALAPPDATA}\Programs\nodejs"
    )
    foreach ($d in $nodeDirs) {
        if (Test-Path (Join-Path $d "npm.cmd")) {
            $env:Path = "$d;" + $env:Path
            break
        }
    }
    $npm = Get-Command npm -ErrorAction SilentlyContinue
}
if (-not $npm) {
    Write-Host "No hay npm/Node en PATH. Instala Node LTS y vuelve a correr este ritual." -ForegroundColor Red
    exit 1
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
        Write-Host "Instala a mano o coloca cloudflared.exe en tools\"
        exit 1
    }
}

Stop-PanelAnterior
Liberar-Puerto -Port $Puerto
Liberar-Puerto -Port 8080

if (-not (Test-Path (Join-Path $Ui "node_modules"))) {
    Write-Host "Instalando piezas del Pergamino (npm install)..."
    Push-Location $Ui
    try {
        & npm.cmd install --no-fund --no-audit
        if ($LASTEXITCODE -ne 0) { throw "npm install fallo" }
    } finally {
        Pop-Location
    }
}

Write-Host "Forjando Cascada (npm run build)..."
Push-Location $Ui
try {
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw "npm run build fallo" }
} finally {
    Pop-Location
}

Write-Host ("Sirviendo Cascada en :{0} ..." -f $Puerto)
$viteOut = Join-Path $LogDir "panel_vite_out.log"
$viteErr = Join-Path $LogDir "panel_vite_err.log"
foreach ($f in @($viteOut, $viteErr)) {
    if (Test-Path $f) { Remove-Item $f -Force }
}
$viteProc = Start-Process -FilePath "npm.cmd" `
    -ArgumentList "run","preview","--","--host","--port","$Puerto" `
    -WorkingDirectory $Ui -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $viteOut -RedirectStandardError $viteErr
Set-Content -Path (Join-Path $Root "data\panel_vite.pid") -Value $viteProc.Id
Start-Sleep -Seconds 3

$tunnelOut = Join-Path $LogDir "cloudflared_pwa_out.log"
$tunnelErr = Join-Path $LogDir "cloudflared_pwa_err.log"
foreach ($f in @($tunnelOut, $tunnelErr)) {
    if (Test-Path $f) { Remove-Item $f -Force }
}
Write-Host "Abriendo tunel Cloudflare (HTTPS) ..."
$tunnelProc = Start-Process -FilePath $cf -ArgumentList "tunnel","--url","http://127.0.0.1:$Puerto" `
    -WorkingDirectory $Root -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $tunnelOut -RedirectStandardError $tunnelErr
Set-Content -Path (Join-Path $Root "data\panel_vite_tunnel.pid") -Value $tunnelProc.Id

$httpsUrl = $null
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    $txt = ""
    if (Test-Path $tunnelErr) {
        $txt += (Get-Content $tunnelErr -Raw -ErrorAction SilentlyContinue)
    }
    if (Test-Path $tunnelOut) {
        $txt += (Get-Content $tunnelOut -Raw -ErrorAction SilentlyContinue)
    }
    if ($txt -match 'https://[a-zA-Z0-9.-]+\.trycloudflare\.com') {
        $httpsUrl = $Matches[0]
        break
    }
}

Write-Host ""
if ($httpsUrl) {
    Write-Host "LISTO - usa ESTA URL en el celular (raiz Cascada, NO dashboard_sombras):" -ForegroundColor Green
    Write-Host ("  {0}" -f $httpsUrl) -ForegroundColor Cyan
    Write-Host ""
    Write-Host "En Android Chrome:"
    Write-Host "  1. Abre la URL https de arriba"
    Write-Host "  2. Toca Beru · El Cazador → ahi va la flota de los 14"
    Write-Host "  3. Menu -> Instalar app (o Anadir a pantalla de inicio)"
    Write-Host "  4. Borra el icono VIEJO (dashboard_sombras / IP http)"
    Write-Host ""
    try { Set-Clipboard -Value $httpsUrl } catch {}
    Write-Host "(URL copiada al portapapeles si se pudo)"
} else {
    Write-Host "Tunel arranco pero no lei la URL a tiempo." -ForegroundColor Yellow
    Write-Host ("Revisa los logs: {0} / {1}" -f $tunnelOut, $tunnelErr)
}

Write-Host ("  Cascada local: http://127.0.0.1:{0}/" -f $Puerto)
Write-Host ("  vite PID {0}" -f $viteProc.Id)
Write-Host ("  cloudflared PID {0}" -f $tunnelProc.Id)
Write-Host "  Detener: .\scripts\detener_panel_win.ps1"
Write-Host ""
