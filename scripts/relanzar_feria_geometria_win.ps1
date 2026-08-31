# Relanzar todo el ejercito feria lineal con geometria nueva (Red simetrica + engorde 0.2%)
param(
    [int]$BatchSize = 25,
    [int]$EscalonSegundos = 30
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$santos = @()
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -match "python" -and
        $_.CommandLine -match "arise_beru_rango_manos" -and
        $_.CommandLine -match "--perfil feria" -and
        $_.CommandLine -notmatch "--mercado inverse"
    } |
    ForEach-Object {
        if ($_.CommandLine -match "--activo (\S+)") {
            $santos += $matches[1].ToUpper()
        }
    }
$santos = @($santos | Sort-Object -Unique)
if ($santos.Count -eq 0) {
    Write-Host "Sin Santos feria vivos" -ForegroundColor Yellow
    exit 0
}

Write-Host "Relanzar $($santos.Count) Santos feria (geometria nueva)" -ForegroundColor Magenta

# Matar todos feria lineal
$kill = @()
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -match "python" -and
        $_.CommandLine -match "arise_beru_rango_manos" -and
        $_.CommandLine -match "--perfil feria" -and
        $_.CommandLine -notmatch "--mercado inverse"
    } |
    ForEach-Object { $kill += $_.ProcessId }
if ($kill.Count) {
    Stop-Process -Id $kill -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    Write-Host "Matados $($kill.Count) procesos feria" -ForegroundColor DarkYellow
}

$lotes = @()
for ($i = 0; $i -lt $santos.Count; $i += $BatchSize) {
    $slice = $santos[$i..([Math]::Min($i + $BatchSize - 1, $santos.Count - 1))]
    $lotes += ,@($slice)
}

$ok = 0; $fail = 0; $n = 1
foreach ($lot in $lotes) {
    Write-Host ""
    Write-Host "=== LOTE $n / $($lotes.Count) ($($lot.Count) Santos) ===" -ForegroundColor Cyan
    $feriaArgs = @{
        Santos          = ($lot -join ",")
        EscalonSegundos = $EscalonSegundos
        SinOjos         = $true
    }
    & (Join-Path $Root "scripts\despertar_santos_feria_win.ps1") @feriaArgs
    Start-Sleep -Seconds 5
    foreach ($s in $lot) {
        $inf = Join-Path $Root "data\beru\rango\$s\manos_feria_informe.json"
        if (Test-Path $inf) {
            $j = Get-Content $inf -Raw | ConvertFrom-Json
            $rl = $j.snapshot.geometria.red_activacion_long_pct
            $rs = $j.snapshot.geometria.red_activacion_short_pct
            $ep = $j.snapshot.geometria.engorde_paso_pct
            if ($j.snapshot.vivo.estado -eq "ACECHANDO" -and $rl -eq $rs -and $ep -eq 0.002) {
                $ok++
            } else {
                $fail++
                Write-Host "  !! $s estado=$($j.snapshot.vivo.estado) red=$rl/$rs eng=$ep" -ForegroundColor Red
            }
        } else {
            $fail++
            Write-Host "  !! $s NO_INF" -ForegroundColor Red
        }
    }
    $n++
}

Write-Host ""
Write-Host "Relanzamiento: OK geom=$ok FAIL=$fail" -ForegroundColor $(if ($fail -eq 0) { "Green" } else { "Yellow" })
