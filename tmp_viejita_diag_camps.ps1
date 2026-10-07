$Root = "C:\Users\lenovo\ShadowHarmy"
Set-Location $Root
$Git = "C:\Program Files\Git\cmd\git.exe"
$Py = "C:\Users\lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe"
Write-Output ("HEAD=" + (& $Git -C $Root log -1 --oneline))
Write-Output ("HAS_SELLAR=" + (Test-Path "$Root\scripts\sellar_viejita_parada_limpia.py"))
Write-Output ("HAS_NETO=" + [bool](Select-String -Path "$Root\core\okx_bridge.py" -Pattern "asegurar_modo_neto" -SimpleMatch -EA SilentlyContinue))
$camps = @(Get-CimInstance Win32_Process -EA SilentlyContinue | Where-Object { $_.CommandLine -and $_.CommandLine -match "arise_beru_rango_campamento" })
Write-Output ("CAMP_PROCS=" + $camps.Count)
& $Py -u -c "from core import okx_rest; c=okx_rest.get_private('/api/v5/account/config') or []; print('modo', (list(c) or [{}])[0].get('posMode')); p=okx_rest.get_private('/api/v5/account/positions', params={'instType':'SWAP'}) or []; print('swap_abiertas', sum(1 for x in p if abs(float(x.get('pos') or 0))>1e-12))"
foreach ($id in @("CAMP_001","CAMP_002","CAMP_010")) {
  $err = Join-Path $Root "data\beru\rango\vigilante_flota\campamentos\$id\stderr.log"
  $out = Join-Path $Root "data\beru\rango\vigilante_flota\campamentos\$id\stdout.log"
  Write-Output ("==== " + $id + " ====")
  if (Test-Path $err) { Get-Content $err -Tail 25 -EA SilentlyContinue }
  if (Test-Path $out) { Get-Content $out -Tail 15 -EA SilentlyContinue }
}
$bat = Get-ChildItem "$Root\data\beru\rango\vigilante_flota\run_CAMP_*.bat" -EA SilentlyContinue | Select-Object -First 1
if ($bat) { Get-Content $bat.FullName }
