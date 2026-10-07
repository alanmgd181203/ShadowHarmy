@echo off
cd /d C:\Users\lenovo\ShadowHarmy
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set IGRIS_ESCUDO_LOG_SOLO_STDOUT=1
set BERU_MAR=okx
set IGRIS_ESCUDO_BTC_ACTIVO=1
set IGRIS_ESCUDO_BTC_MODO=live
set IGRIS_ESCUDO_BTC_LIVE_OK=1
set IGRIS_ESCUDO_BTC_R=dinamico
set IGRIS_ESCUDO_BTC_FRENTE=inverso
set IGRIS_ESCUDO_BTC_ORD_TIPO=market
set IGRIS_ESCUDO_BTC_PELDANO_USD=250
set IGRIS_ESCUDO_BTC_ACTIVAR_USD=500
set IGRIS_ESCUDO_BTC_POLVO_USD=250
set IGRIS_ESCUDO_BTC_VEDA_S=25
set IGRIS_ESCUDO_BTC_LIMIT_ESPERA_S=8
set IGRIS_ESCUDO_BTC_LIMIT_PASO_PCT=0.0015
set IGRIS_ESCUDO_BTC_LIMIT_MAX_DRIFT_PCT=0.02
set IGRIS_ESCUDO_BTC_LIMIT_MAX_MOVES=40
set IGRIS_ESCUDO_BTC_LIMIT_OFFSET_PCT=0.00015
set PY=C:\Users\lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe
set SCRIPT=C:\Users\lenovo\ShadowHarmy\scripts\arise_igris_escudo_btc.py
set OUTLOG=C:\Users\lenovo\ShadowHarmy\data\logs\arise_igris_escudo_out.log
set ERRLOG=C:\Users\lenovo\ShadowHarmy\data\logs\arise_igris_escudo_err.log
"%PY%" -u "%SCRIPT%" --intervalo 15 >> "%OUTLOG%" 2>> "%ERRLOG%"
