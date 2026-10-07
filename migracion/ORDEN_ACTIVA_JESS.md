# ORDEN ACTIVA (única)

**Puerta oficial Jess / Cursor México (viejita).**  
Siempre el mismo path: `migracion/ORDEN_ACTIVA_JESS.md`  
Los `PEGAR_JESS_*` son **recetas** (anexo). No son la puerta.

**Actualización 2026-10-07 — cirugía flota: huérfanos + techo masa al armar**

---

## 1) Arranque (obligatorio)

```
git fetch origin
git checkout regalo
git pull origin regalo
```

Luego **abre solo este archivo** y ejecuta la misión de abajo.

---

## 2) Misión — cirugía completa del ejército Beru

**Qué es:** Tras reinicio torcido quedó ~80 bolsas SWAP huérfanas (mente ACECHANDO con bolsa abierta) y AEON armó Red con masa loca. Hay que: traer código con **techo $25 al armar**, apagar, aplanar todo SWAP (no BTC spot), sellar, despertar **desde cero**.

**Receta / detalle:** ninguna. (USA puede haber corrido ya el ritual; si HEAD ya tiene el techo y flota limpia, solo confirmar.)

### Comandos exactos (PowerShell, raíz del repo en la viejita)

```
cd C:\Users\lenovo\ShadowHarmy
git fetch origin
git checkout regalo
git pull origin regalo

# Confirmar techo anti-tumor
Select-String -Path core\beru_rango.py -Pattern "masa_armar_max_usd" -SimpleMatch
Select-String -Path core\config.py -Pattern "MASA_ARMAR_MAX_USD" -SimpleMatch

# Ritual completo (apaga · aplana SWAP · neto · sellar · despertar desde cero)
powershell -NoProfile -ExecutionPolicy Bypass -File tmp_viejita_recuperar_despertar.ps1
```

Si falta `tmp_aplanar_todo_salvo_btc_spot.py` en la viejita, USA lo deja por SCP antes; sin aplanar no despertar.

Espera el despertar (~2–3 min). Luego:

```
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\_pulso_despertar.ps1
```

---

## 3) Qué NO hacer

- No `--continuar` (debe ser **desde cero**).
- No dejar manos sueltas encima de cuarteles.
- No tocar `.env` ni BTC spot.
- No volver a piernas / `long_short_mode`.

---

## 4) Qué mirar al terminar

1. HEAD con techo `MASA_ARMAR_MAX` / `masa_armar_max_usd`.
2. `swap_abiertas` ~0 justo tras aplanar; luego solo lo que Beru abra chico.
3. 28 cuarteles vivos, 0 manos sueltas.
4. Avisar al Monarca: cuarteles, SWAP abiertas, si Igris late.

---

## 5) HECHO (Jess / Cursor marca)

- [ ] pull regalo hecho
- [ ] techo masa confirmado
- [ ] aplanar + despertar desde cero
- [ ] pulso OK · Monarca avisado
