# Shadow Army — Preparar migración Beru NORMAL → FERIA (sin ejecutar wake)
# Escanea manos lineales en perfil normal, excluye los que ya corren feria,
# escribe manifiesto + listas para el GO del Monarca.
#
# Uso:
#   .\scripts\preparar_migracion_normal_a_feria_win.ps1
#   .\scripts\preparar_migracion_normal_a_feria_win.ps1 -BatchSize 20
param(
    [int]$BatchSize = 25,
    [string]$OutDir = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not $OutDir) {
    $OutDir = Join-Path $Root "data\beru\rango"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$normal = @{}
$feria = @{}
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -match "python" -and
        $_.CommandLine -match "arise_beru_rango_manos" -and
        $_.CommandLine -notmatch "--mercado inverse"
    } |
    ForEach-Object {
        if ($_.CommandLine -match "--activo (\S+)") {
            $a = $matches[1].ToUpper()
            if ($_.CommandLine -match "--perfil feria") {
                $feria[$a] = $_.ProcessId
            } else {
                $normal[$a] = $_.ProcessId
            }
        }
    }

$migrar = @($normal.Keys | Sort-Object)
$yaFeria = @($feria.Keys | Sort-Object)
$listaCsv = $migrar -join ","
$ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Lotes para escalon (evitar tormenta de 135 procesos de golpe)
$lotes = @()
for ($i = 0; $i -lt $migrar.Count; $i += $BatchSize) {
    $slice = $migrar[$i..([Math]::Min($i + $BatchSize - 1, $migrar.Count - 1))]
    $lotes += ,@($slice)
}

$manifest = [ordered]@{
    ts_utc           = $ts
    estado           = "PREPARADO_SIN_MIGRAR"
    perfil_origen    = "normal"
    perfil_destino   = "feria"
    n_migrar         = $migrar.Count
    n_ya_feria       = $yaFeria.Count
    santos_migrar    = $migrar
    pids_normal      = $normal
    santos_ya_feria  = $yaFeria
    geometria_feria  = @{
        vacio_pct    = "2.4%"
        oz_gap_pct   = "0.4%"
        red_pct      = "1.4% simetrica (LONG = SHORT)"
        engorde      = "+$1 / 0.2% (feria; normal canonico tambien 0.2% segun Monarca)"
        masa         = "$5"
    }
    ritual = @(
        "1. git pull (traer Red simetrica + teatro del otro Cursor)"
        "2. Por lote: matar manos NORMAL del lote (PIDs en pids_normal)"
        "3. .\scripts\despertar_santos_feria_win.ps1 -Santos <lote> -SinOjos"
        "4. Revisar manos_feria_stderr.log · informe ACECHANDO · 0 errores"
        "5. NO tocar manos_informe.json (sellos normal quedan como archivo muerto)"
    )
    lotes_ps1 = @(
        foreach ($lot in $lotes) {
            ".\\scripts\\despertar_santos_feria_win.ps1 -Santos `"$($lot -join ',')`" -SinOjos"
        }
    )
}

$jsonPath = Join-Path $OutDir "migracion_normal_a_feria.json"
$txtPath = Join-Path $OutDir "migracion_normal_a_feria_lista.txt"
$mdPath = Join-Path $OutDir "MIGRACION_NORMAL_A_FERIA.md"

$manifest | ConvertTo-Json -Depth 6 | Set-Content -Path $jsonPath -Encoding UTF8
$listaCsv | Set-Content -Path $txtPath -Encoding UTF8

$md = @()
$md += "# Migracion Beru NORMAL -> FERIA (preparado, sin GO)"
$md += ""
$md += "Generado: $ts"
$md += ""
$md += "## Por que feria en caida BTC"
$md += ""
$md += "- Vacio/Sangre 2,4% (vs 1,2%) - menos entradas en ruido bajista."
$md += "- Red 1,4% simetrica LONG = SHORT (feria; normal 0,7% simetrica)."
$md += "- Engorde +1 USD / 0,2% por peldaño (doctrina Monarca; no 0,1%)."
$md += "- Sellos aislados (manos_feria_*) - no pisa el normal archivado."
$md += ""
$md += "## Estado escaneo"
$md += ""
$md += "- Santos a migrar: $($migrar.Count)"
$md += "- Ya en feria: $($yaFeria.Count)"
$md += "- Lotes de $BatchSize : $($lotes.Count)"
$md += ""
$md += "## Ya feria (saltar)"
$md += ""
$md += ($yaFeria -join ", ")
$md += ""
$md += "## Ritual por lote"
$md += ""

$i = 1
foreach ($lot in $lotes) {
    $md += "### Lote $i ($($lot.Count) Santos)"
    $md += ""
    $pids = ($lot | ForEach-Object { if ($normal.ContainsKey($_)) { $normal[$_] } }) -join ","
    $md += "# Matar normal: Stop-Process -Id $pids -Force"
    $md += ".\scripts\despertar_santos_feria_win.ps1 -Santos `"$($lot -join ',')`" -SinOjos"
    $md += ""
    $i++
}

$md += "---"
$md += ""
$md += "Lista completa: $txtPath"
$md += "JSON: $jsonPath"

$md -join "`n" | Set-Content -Path $mdPath -Encoding UTF8

Write-Host ""
Write-Host "=== PREPARAR MIGRACION NORMAL -> FERIA ===" -ForegroundColor Magenta
Write-Host "  Migrar: $($migrar.Count) Santos" -ForegroundColor Cyan
Write-Host "  Ya feria: $($yaFeria.Count) ($($yaFeria -join ', '))" -ForegroundColor DarkGray
Write-Host "  Lotes: $($lotes.Count) x ~$BatchSize" -ForegroundColor Gray
Write-Host "  Manifiesto: $jsonPath" -ForegroundColor Green
Write-Host "  Runbook:    $mdPath" -ForegroundColor Green
Write-Host "  NO se migro nada. Di GO cuando quieras ejecutar." -ForegroundColor Yellow
Write-Host ""
