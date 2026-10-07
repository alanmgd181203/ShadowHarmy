# Corre EN la viejita: pull regalo + sellar + despertar limpio desde 0.
$ErrorActionPreference = "Continue"
$Root = "C:\Users\lenovo\ShadowHarmy"
$Git = "C:\Program Files\Git\cmd\git.exe"
$Py = "C:\Users\lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe"
Set-Location $Root

Write-Output ("HOST=" + $env:COMPUTERNAME)
& $Git fetch origin
& $Git checkout regalo
& $Git pull origin regalo
Write-Output ("HEAD=" + (& $Git log -1 --oneline))

Write-Output "=== MODO CASA ==="
& $Py -u -c "from core import okx_rest; c=okx_rest.get_private('/api/v5/account/config') or []; print('modo', (list(c) or [{}])[0].get('posMode')); p=okx_rest.get_private('/api/v5/account/positions', params={'instType':'SWAP'}) or []; print('swap_abiertas', sum(1 for x in p if abs(float(x.get('pos') or 0))>1e-12))"

Write-Output "=== SELLAR ESCUDO ==="
& $Py -u scripts\sellar_viejita_parada_limpia.py

Write-Output "=== IRON MEMORIA CERO ==="
& $Py -u -c "from pathlib import Path; Path('data/beru/papel').mkdir(parents=True, exist_ok=True); Path('data/beru/papel/iron_memoria.json').write_text('{}', encoding='utf-8'); Path('data/beru/papel/descarga_estado.json').write_text('{}', encoding='utf-8'); print('iron_memoria_cero')"

Write-Output "=== DESPERTAR EJERCITO ==="
& powershell -NoProfile -ExecutionPolicy Bypass -File "$Root\scripts\_despertar_ejercito.ps1"
$wakeExit = $LASTEXITCODE
Write-Output ("WAKE_EXIT=" + $wakeExit)

Start-Sleep -Seconds 5
Write-Output "=== PULSO ==="
if (Test-Path "$Root\scripts\_pulso_despertar.ps1") {
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$Root\scripts\_pulso_despertar.ps1"
}

# Confirmar desde-cero en un bat de cuartel
$bat = Get-ChildItem "$Root\data\beru\rango\vigilante_flota\run_CAMP_*.bat" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($bat) {
  Write-Output ("BAT_SAMPLE=" + $bat.FullName)
  Select-String -Path $bat.FullName -Pattern "desde-cero|continuar" | ForEach-Object { Write-Output $_.Line }
}

exit $wakeExit
