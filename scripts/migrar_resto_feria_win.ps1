$ErrorActionPreference = "Stop"
$Root = "C:\Users\lenovo\ShadowHarmy"
Set-Location $Root

$lotes = @(
    "BMNR,BSP,CBRS,CC,CFG,CHIP,CIEN,COHR,CRCL,CRDO,CROSS,CRV,CRWV,CVX,DASH,DOGE,DOS,DOT,DRAM,ESP,ETC,EUL,FIL,FLNC,FLY",
    "FWDI,GIGADEVICE,GIGGLE,GLW,GMT,HPE,HYPE,HYUNDAI,INTC,INTW,KITE,KNC,KORU,KSM,LINK,LIT,LRCX,LSK,MARA,MET,MINIMAX,MNT,MON,MORPHO,MOVR",
    "MRVL,MSTR,MUBARAK,MUU,MVLL,NBIS,NEAR,NIL,O,OKB,ONDS,OP,ORCL,PENGSTOCK,PEOPLE,PIEVERSE,PLTR,POLYX,POPCAT,PRL,PURR,QNTX,RDW,RKLB,ROBO",
    "ROSE,RPL,SAFE,SAMSUNG,SHAZ,SKHY,SKHYNIX,SKUU,SMCI,SNXX,SOL,SOXL,SOXS,SPACE,SSPC,STXX,SUI,SUSHI,SYRUP,TAO,TER,TRB,TSEM,TSLL,TWT",
    "UB,UNI,USAR,VVV,WDC,XLM,ZBCN,ZBT,ZEREBRO,ZHIPU"
)

$i = 2
$totalOk = 25
$totalFail = 0
foreach ($lote in $lotes) {
    Write-Host ""
    Write-Host "########## LOTE $i ##########" -ForegroundColor Magenta
    & "$Root\scripts\migrar_lote_normal_a_feria_win.ps1" -Santos $lote -SinOjos
    if ($LASTEXITCODE -ne 0) { Write-Host "LOTE $i exit $LASTEXITCODE" -ForegroundColor Red }
    $i++
}

Write-Host ""
Write-Host "=== MIGRACION LOTES 2-6 COMPLETA ===" -ForegroundColor Green
