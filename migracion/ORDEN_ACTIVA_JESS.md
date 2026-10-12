# ORDEN ACTIVA (única)

**Puerta oficial Jess / Cursor México (viejita).**  
Siempre el mismo path: `migracion/ORDEN_ACTIVA_JESS.md`  
Los `PEGAR_JESS_*` son **recetas** (anexo). No son la puerta.

**Actualización 2026-10-12 — solo traer código de cirugías engorde/Iron (SIN despertar)**

---

## 1) Arranque (obligatorio)

```
git fetch origin
git checkout regalo
git pull origin regalo
```

Luego **abre solo este archivo** y ejecuta la misión de abajo.

---

## 2) Misión — preparar migración (código listo, ejército dormido en este paso)

**Qué es:** Traer a la viejita el paquete de cirugías ya sellado en USA:
1. Memoria del engorde hasta vacío de sangre  
2. Campos Iron ×1 / ×2 / ×3 (1 % y 5 % sobre **posición actual**, no pierna histórica)  
3. Red short: planta 0,8 / engorda como 0,7  

**Solo pull + comprobar que el código llegó.**  
**No despertar Beru, no tocar manos, no aplanar, no reiniciar flota, no Iron live agresivo.**

**Receta / detalle:** `PLAN_CIRUGIA_ENGORDE_IRON_CAMPOS_2026-10-12.md`  
**Checkpoint si hay que volver:** tag `checkpoint-pre-cirugias-engorde-iron-2026-10-12`

### Comandos exactos (PowerShell, raíz del repo en la viejita)

```
cd C:\Users\lenovo\ShadowHarmy
git fetch origin
git checkout regalo
git pull origin regalo

# Confirmar HEAD reciente (debe mencionar cirugia engorde / campo Iron)
git log -5 --oneline

# Brújula Iron: % sobre posición actual
Select-String -Path cirugias\hiron\campo_masa.py -Pattern "posicion_usd" -SimpleMatch
Select-String -Path cirugias\hiron\campo_masa.py -Pattern "SANGRE_PCT" -SimpleMatch

# Memoria engorde (no recetear en cada Oz)
Select-String -Path core\beru_rango.py -Pattern "engorde_memoria_peldaños" -SimpleMatch
Select-String -Path core\beru_rango.py -Pattern "limpiar_engorde_campana" -SimpleMatch

# Red short sorda
Select-String -Path core\beru_rango.py -Pattern "peldaños_holgura_red_short" -SimpleMatch

# Humo en seco (no toca exchange ni despierta)
$env:PYTHONIOENCODING = "utf-8"
python scripts\validar_beru_cirugia_engorde_iron_smoke.py
```

Si el smoke sale `[SMOKE] OK` y los `Select-String` encuentran las piezas → migración de **código** lista.

---

## 3) Qué NO hacer

- **No despertar** Beru / cuarteles / campamentos.
- **No** `arise_*_manos`, **no** ritual recuperar/despertar, **no** aplanar SWAP.
- **No** reiniciar Igris / Iron / escudo / susurro “por si acaso”.
- **No** tocar `.env`, secretos, ranking, ni BTC spot.
- **No** `--continuar` ni `--desde-cero` de flota en este paso.

---

## 4) Qué mirar al terminar

1. `git log -1` en `regalo` con el commit de campo Iron / cirugías engorde.  
2. Smoke `[SMOKE] OK`.  
3. Avisar al Monarca en una frase:  
   - pull OK / HEAD corto  
   - smoke OK o fallo  
   - confirmar: **nada despertado**

---

## 5) HECHO (Jess / Cursor marca)

- [ ] pull `regalo` hecho
- [ ] piezas de código confirmadas (campo / memoria / red sorda)
- [ ] smoke cirugia OK
- [ ] **nada despertado** · Monarca avisado
