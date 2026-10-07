# EN la viejita: apaga, fuerza código regalo (sin tocar .env), sellar, despertar desde 0.
$ErrorActionPreference = "Continue"
$Root = "C:\Users\lenovo\ShadowHarmy"
$Git = "C:\Program Files\Git\cmd\git.exe"
$Py = "C:\Users\lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe"
Set-Location $Root

Write-Output ("HOST=" + $env:COMPUTERNAME)

# 1) Apagar ejército
if (Test-Path "$Root\scripts\_apagar_ejercito.ps1") {
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$Root\scripts\_apagar_ejercito.ps1"
} else {
  Get-CimInstance Win32_Process -EA SilentlyContinue | Where-Object {
    $_.CommandLine -and $_.CommandLine -match "arise_beru_rango|arise_igris_escudo|arise_desinflar|arise_extasis|arise_papel|arise_descarga|vigilar_neto|vigilar_palanca"
  } | ForEach-Object {
    taskkill /PID $_.ProcessId /F 2>$null | Out-Null
  }
}
Start-Sleep -Seconds 4
Write-Output ("TRAS_APAGAR camp=" + @(Get-CimInstance Win32_Process -EA SilentlyContinue | Where-Object { $_.CommandLine -match "arise_beru_rango_campamento" }).Count)

# 2) Forzar código regalo (guarda .env)
$envBak = Join-Path $env:TEMP ("shadowharmy_env_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".bak")
if (Test-Path "$Root\.env") { Copy-Item "$Root\.env" $envBak -Force; Write-Output ("ENV_BAK=" + $envBak) }

& $Git fetch origin
# Limpia untracked NO ignorados (cirugias sueltas, etc). data/ y .env suelen estar en gitignore → se quedan.
& $Git clean -fd
& $Git checkout -B regalo origin/regalo
& $Git reset --hard origin/regalo
Write-Output ("HEAD=" + (& $Git log -1 --oneline))
Write-Output ("BRANCH=" + (& $Git branch --show-current))

# Grep doctrina neto en puente
$hit = Select-String -Path "$Root\core\okx_bridge.py" -Pattern "asegurar_modo_neto" -SimpleMatch -ErrorAction SilentlyContinue
Write-Output ("PUENTE_NETO=" + [bool]$hit)
$hit2 = Select-String -Path "$Root\tmp_despertar_cuarteles.py" -Pattern "desde-cero" -SimpleMatch -ErrorAction SilentlyContinue
Write-Output ("DESDE_CERO_EN_BAT_SCRIPT=" + [bool]$hit2)

if (Test-Path $envBak) {
  if (-not (Test-Path "$Root\.env")) { Copy-Item $envBak "$Root\.env" -Force; Write-Output "ENV_RESTAURADO" }
}

Write-Output "=== MODO CASA ==="
& $Py -u -c "from core import okx_rest; c=okx_rest.get_private('/api/v5/account/config') or []; print('modo', (list(c) or [{}])[0].get('posMode')); p=okx_rest.get_private('/api/v5/account/positions', params={'instType':'SWAP'}) or []; print('swap_abiertas', sum(1 for x in p if abs(float(x.get('pos') or 0))>1e-12))"

if (-not $hit) {
  Write-Output "ABORT_SIN_CODIGO_NETO"
  exit 9
}

Write-Output "=== SELLAR ESCUDO ==="
& $Py -u scripts\sellar_viejita_parada_limpia.py

Write-Output "=== IRON MEMORIA CERO ==="
& $Py -u -c "from pathlib import Path; Path('data/beru/papel').mkdir(parents=True, exist_ok=True); Path('data/beru/papel/iron_memoria.json').write_text('{}', encoding='utf-8'); Path('data/beru/papel/descarga_estado.json').write_text('{}', encoding='utf-8'); print('iron_memoria_cero')"

Write-Output "=== DESPERTAR ==="
& powershell -NoProfile -ExecutionPolicy Bypass -File "$Root\scripts\_despertar_ejercito.ps1"
$wakeExit = $LASTEXITCODE
Write-Output ("WAKE_EXIT=" + $wakeExit)

Start-Sleep -Seconds 6
if (Test-Path "$Root\scripts\_pulso_despertar.ps1") {
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$Root\scripts\_pulso_despertar.ps1"
}

$bat = Get-ChildItem "$Root\data\beru\rango\vigilante_flota\run_CAMP_*.bat" -EA SilentlyContinue | Select-Object -First 1
if ($bat) {
  Write-Output ("BAT=" + $bat.Name)
  Select-String -Path $bat.FullName -Pattern "desde-cero|continuar" | ForEach-Object { Write-Output ("BAT_LINE=" + $_.Line.Trim()) }
}

exit $wakeExit
