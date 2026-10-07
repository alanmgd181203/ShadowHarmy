# Despierta todos los generales en la viejita (misma formacion que antes del apagon).
# No enciende extasis vivo. Igris BTC/bolsa como estaban (live mercado).
$ErrorActionPreference = "Continue"
$Root = "C:\Users\lenovo\ShadowHarmy"
$Py = "C:\Users\lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe"
Set-Location $Root

function Start-Bat([string]$BatPath, [string]$Nombre, [string]$YaPat = "") {
  if (-not (Test-Path $BatPath)) {
    Write-Output ("FALTA_BAT " + $Nombre + " " + $BatPath)
    return
  }
  if ($YaPat -and (Count-Match $YaPat) -gt 0) {
    Write-Output ("YA " + $Nombre + " n=" + (Count-Match $YaPat))
    return
  }
  $cmd = 'cmd.exe /c "' + $BatPath + '"'
  $r = ([wmiclass]"Win32_Process").Create($cmd)
  Write-Output ("LANZA " + $Nombre + " ret=" + $r.ReturnValue + " pid=" + $r.ProcessId)
}

function Count-Match([string]$Pat) {
  return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -and $_.CommandLine -match $Pat
  }).Count
}

Write-Output ("HOST=" + $env:COMPUTERNAME)
Write-Output ("ANTES camp=" + (Count-Match "arise_beru_rango_campamento") + " manos=" + (Count-Match "arise_beru_rango_manos") + " igris=" + (Count-Match "arise_igris_escudo"))

# --- Beru: cuarteles del manifiesto ---
Write-Output "=== BERU CUARTELES ==="
& $Py -u tmp_despertar_cuarteles.py
if ($LASTEXITCODE -ne 0) {
  Write-Output ("BERU_FALLO exit=" + $LASTEXITCODE)
}

# --- Igris escudo BTC (live, schtask) ---
Write-Output "=== IGRIS BTC ==="
if ((Count-Match "arise_igris_escudo_btc") -lt 1) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$Root\tmp_viejita_schtask_market.ps1"
} else {
  Write-Output "IGRIS_BTC_YA"
}

# --- Igris bolsa ---
Write-Output "=== IGRIS BOLSA ==="
Start-Bat "$Root\cirugias\escudo_dual\run_escudo_bolsa_papel.bat" "igris_bolsa" "arise_igris_escudo_bolsa"

# --- Desinflar papel / taxonomia ---
Write-Output "=== DESINFLAR PAPEL ==="
Start-Bat "$Root\cirugias\escudo_dual\run_desinflar_papel.bat" "desinflar" "arise_desinflar_papel"

# --- Extasis papel (nunca vivo) ---
Write-Output "=== EXTASIS PAPEL ==="
Start-Bat "$Root\cirugias\escudo_dual\run_extasis_papel.bat" "extasis_papel" "arise_extasis_papel"

# --- Iron papel + descarga ---
Write-Output "=== IRON ==="
$logs = Join-Path $Root "data\logs"
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$papelDir = Join-Path $Root "data\beru\papel"
New-Item -ItemType Directory -Force -Path $papelDir | Out-Null

$batPapel = Join-Path $Root "cirugias\hiron\run_arise_papel.bat"
@(
  "@echo off",
  "cd /d C:\Users\lenovo\ShadowHarmy",
  "set BERU_MAR=okx",
  "set PYTHONUTF8=1",
  "`"$Py`" -u cirugias\hiron\arise_papel.py 1>> data\logs\arise_papel.log 2>>&1"
) | Set-Content -Encoding ASCII $batPapel

$batDesc = Join-Path $Root "cirugias\hiron\run_arise_descarga.bat"
@(
  "@echo off",
  "cd /d C:\Users\lenovo\ShadowHarmy",
  "set BERU_MAR=okx",
  "set PYTHONUTF8=1",
  "`"$Py`" -u cirugias\hiron\arise_descarga.py 1>> data\logs\arise_descarga.log 2>>&1"
) | Set-Content -Encoding ASCII $batDesc

Start-Bat $batPapel "iron_papel" "arise_papel\.py"
Start-Bat $batDesc "iron_descarga" "arise_descarga\.py"

# --- Vigilantes ---
Write-Output "=== VIGILANTES ==="
Start-Bat "$Root\scripts\run_vigilar_neto.bat" "vigilar_neto" "vigilar_neto_telegram"
Start-Bat "$Root\scripts\run_vigilar_palanca.bat" "vigilar_palanca" "vigilar_palanca_okx"

# --- Reloj sala (una mirada; no daemon) ---
Write-Output "=== RELOJ SALA ==="
& $Py -u cirugias\sala_por_color\reloj_cuota.py 2>> data\beru\sala_cuota\reloj.err
Write-Output ("reloj_exit=" + $LASTEXITCODE)

Start-Sleep -Seconds 8

Write-Output "=== CONTEO FINAL ==="
Write-Output ("camp=" + (Count-Match "arise_beru_rango_campamento"))
Write-Output ("manos=" + (Count-Match "arise_beru_rango_manos"))
Write-Output ("igris_btc=" + (Count-Match "arise_igris_escudo_btc"))
Write-Output ("igris_bolsa=" + (Count-Match "arise_igris_escudo_bolsa"))
Write-Output ("desinflar=" + (Count-Match "arise_desinflar_papel"))
Write-Output ("extasis=" + (Count-Match "arise_extasis_papel"))
Write-Output ("iron_papel=" + (Count-Match "arise_papel\.py"))
Write-Output ("iron_descarga=" + (Count-Match "arise_descarga\.py"))
Write-Output ("neto=" + (Count-Match "vigilar_neto_telegram"))
Write-Output ("palanca=" + (Count-Match "vigilar_palanca_okx"))

$n = Count-Match "arise_beru_rango_campamento|arise_beru_rango_manos|arise_igris_escudo|arise_desinflar|arise_extasis|arise_papel\.py|arise_descarga\.py|vigilar_neto|vigilar_palanca"
Write-Output ("TOTAL_GENERALES_PROC=" + $n)
if ((Count-Match "arise_beru_rango_campamento") -lt 1) { exit 2 }
if ((Count-Match "arise_igris_escudo_btc") -lt 1) { exit 3 }
Write-Output "OK_EJERCITO_DESPIERTO"
exit 0
