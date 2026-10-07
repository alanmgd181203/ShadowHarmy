# EN viejita: apaga, aplana SWAP, fuerza neto + código regalo, despertar limpio.
$ErrorActionPreference = "Continue"
$Root = "C:\Users\lenovo\ShadowHarmy"
$Git = "C:\Program Files\Git\cmd\git.exe"
$Py = "C:\Users\lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe"
Set-Location $Root

Write-Output ("HOST=" + $env:COMPUTERNAME)

# Apagar
if (Test-Path "$Root\scripts\_apagar_ejercito.ps1") {
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$Root\scripts\_apagar_ejercito.ps1"
} else {
  Get-CimInstance Win32_Process -EA SilentlyContinue | Where-Object {
    $_.CommandLine -and $_.CommandLine -match "arise_beru_rango|arise_igris_escudo|arise_desinflar|arise_extasis|arise_papel|arise_descarga|vigilar_neto|vigilar_palanca"
  } | ForEach-Object { taskkill /PID $_.ProcessId /F 2>$null | Out-Null }
}
Start-Sleep -Seconds 5
Write-Output ("CAMP_TRAS_APAGAR=" + @(Get-CimInstance Win32_Process -EA SilentlyContinue | Where-Object { $_.CommandLine -match "arise_beru_rango_campamento" }).Count)

# Código fresco
& $Git fetch origin
& $Git reset --hard origin/regalo
& $Git checkout -B regalo origin/regalo
Write-Output ("HEAD=" + (& $Git log -1 --oneline))
Write-Output ("HAS_PISO=" + [bool](Select-String -Path "$Root\core\lote_okx.py" -Pattern "def asegurar_piso_okx" -SimpleMatch -EA SilentlyContinue))
Write-Output ("HAS_NETO=" + [bool](Select-String -Path "$Root\core\okx_bridge.py" -Pattern "asegurar_modo_neto" -SimpleMatch -EA SilentlyContinue))

# Aplanar basura SWAP (no BTC spot)
if (Test-Path "$Root\tmp_aplanar_todo_salvo_btc_spot.py") {
  Write-Output "=== APLANAR ==="
  & $Py -u "$Root\tmp_aplanar_todo_salvo_btc_spot.py"
} elseif (Test-Path "C:\Users\lenovo\tmp_aplanar_todo_salvo_btc_spot.py") {
  Copy-Item "C:\Users\lenovo\tmp_aplanar_todo_salvo_btc_spot.py" "$Root\tmp_aplanar_todo_salvo_btc_spot.py" -Force
  & $Py -u "$Root\tmp_aplanar_todo_salvo_btc_spot.py"
} else {
  Write-Output "SIN_APLANAR_SCRIPT"
}

# Forzar neto
Write-Output "=== FORZAR NETO ==="
& $Py -u -c @"
from core import okx_rest
c = okx_rest.get_private('/api/v5/account/config') or []
modo = (list(c) or [{}])[0].get('posMode')
print('modo_antes', modo)
p = okx_rest.get_private('/api/v5/account/positions', params={'instType': 'SWAP'}) or []
n = sum(1 for x in p if abs(float(x.get('pos') or 0)) > 1e-12)
print('swap_abiertas', n)
if modo != 'net_mode' and n == 0:
    try:
        r = okx_rest.post_private('/api/v5/account/set-position-mode', {'posMode': 'net_mode'})
        print('switch', r)
    except Exception as e:
        print('switch_err', e)
elif modo != 'net_mode':
    print('NO_SWITCH_HAY_POS')
c2 = okx_rest.get_private('/api/v5/account/config') or []
print('modo_despues', (list(c2) or [{}])[0].get('posMode'))
"@

if (-not (Select-String -Path "$Root\core\lote_okx.py" -Pattern "def asegurar_piso_okx" -SimpleMatch -EA SilentlyContinue)) {
  Write-Output "ABORT_SIN_PISO"
  exit 9
}

Write-Output "=== SELLAR ==="
& $Py -u scripts\sellar_viejita_parada_limpia.py
& $Py -u -c "from pathlib import Path; Path('data/beru/papel').mkdir(parents=True, exist_ok=True); Path('data/beru/papel/iron_memoria.json').write_text('{}', encoding='utf-8'); Path('data/beru/papel/descarga_estado.json').write_text('{}', encoding='utf-8'); print('iron_ok')"

Write-Output "=== DESPERTAR ==="
& powershell -NoProfile -ExecutionPolicy Bypass -File "$Root\scripts\_despertar_ejercito.ps1"
$ex = $LASTEXITCODE
Write-Output ("WAKE_EXIT=" + $ex)
Start-Sleep -Seconds 8
if (Test-Path "$Root\scripts\_pulso_despertar.ps1") {
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$Root\scripts\_pulso_despertar.ps1"
}
$nCamp = @(Get-CimInstance Win32_Process -EA SilentlyContinue | Where-Object { $_.CommandLine -match "arise_beru_rango_campamento" }).Count
Write-Output ("CAMP_FINAL=" + $nCamp)
$bat = Get-ChildItem "$Root\data\beru\rango\vigilante_flota\run_CAMP_*.bat" -EA SilentlyContinue | Select-Object -First 1
if ($bat) { Select-String -Path $bat.FullName -Pattern "desde-cero|continuar" | ForEach-Object { Write-Output ("BAT=" + $_.Line.Trim()) } }
& $Py -u -c "from core import okx_rest; print('modo', (list(okx_rest.get_private('/api/v5/account/config') or [{}])[0].get('posMode'))"
exit $ex
