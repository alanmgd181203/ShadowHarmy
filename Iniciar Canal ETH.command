#!/bin/bash
# Canal paralelo Igris — manto dual ETH exclusivo · MNTUSD colateral intocable
cd "$(dirname "$0")"
export IGRIS_ACTIVOS_EXCLUSIVOS=ETH
export IGRIS_PROTEGER_BASES=MNT
export IGRIS_PROTEGER_SYMBOLS=MNTUSD
export TICKER_BASE=ETH
mkdir -p data/logs/arise_igris
LOG="data/logs/arise_igris/eth_canal_$(date +%Y%m%d_%H%M%S).log"
echo "Arrancando canal ETH → $LOG"
echo "PID will follow. Cierra esta ventana = puede cortar el ritual; mejor minimizar."
/usr/bin/caffeinate -i /Library/Frameworks/Python.framework/Versions/3.14/bin/python3 -u scripts/arise_igris.py --permitir-mainnet-manos --horas 12.0 2>&1 | tee -a "$LOG"
