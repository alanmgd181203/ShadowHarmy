# ORDEN ACTIVA (única)

**Puerta oficial Jess / Cursor México (viejita).**  
Siempre el mismo path: `migracion/ORDEN_ACTIVA_JESS.md`  
Los `PEGAR_JESS_*` son **recetas** (anexo). No son la puerta.

**Actualización 2026-10-12 — preparar ejército para CONTINUAR (SIN despertar)**

---

## 1) Arranque (obligatorio)

```
git fetch origin
git checkout regalo
git pull origin regalo
```

Luego **abre solo este archivo** y ejecuta la misión de abajo.

---

## 2) Misión — preparar al ejército nuevo (saber dónde se quedó)

**Qué es:** Traer el código de las cirugías y **dejar el mapa listo** para cuando el Monarca diga despertar con **`--continuar`** (retomar sello / memoria / saco).  
El ejército nuevo debe saber dónde se quedó; **no** nacer de semilla a ciegas.

**Este paso NO despierta a nadie.**

**Receta:** `PLAN_CIRUGIA_ENGORDE_IRON_CAMPOS_2026-10-12.md`  
**Checkpoint:** `checkpoint-pre-cirugias-engorde-iron-2026-10-12`

### Comandos exactos (PowerShell, raíz del repo en la viejita)

```
cd C:\Users\lenovo\ShadowHarmy
git fetch origin
git checkout regalo
git pull origin regalo

git log -3 --oneline

# Humo frío de las cirugías
$env:PYTHONIOENCODING = "utf-8"
python scripts\validar_beru_cirugia_engorde_iron_smoke.py

# Auditoría de sellos + carpeta Iron + informe (NO despierta)
python scripts\preparar_migracion_continuar_cirugia.py
```

Lee al final el informe:
`data\beru\preparar_continuar_cirugia.json`

---

## 3) Qué NO hacer

- **No despertar** campamentos / manos / `--manos-go`.
- **No** `--desde-cero` ni aplanar SWAP.
- **No** reiniciar Igris / Iron / escudo / susurro.
- **No** tocar `.env` ni secretos.
- Cuando más adelante el Monarca diga GO: será **`--continuar`**, nunca semilla limpia en este pase.

---

## 4) Qué mirar al terminar

1. Smoke `[SMOKE] OK`.  
2. Prep `[PREP] OK` y resumen: cuántos sellos pueden continuar / cuántos ya traen memoria de engorde.  
3. Avisar al Monarca:
   - HEAD corto  
   - `pueden_continuar` / `con_memoria_engorde` / `solo_semilla`  
   - confirmar: **nada despertado**

---

## 5) HECHO (Jess / Cursor marca)

- [ ] pull `regalo` hecho
- [ ] smoke cirugia OK
- [ ] `preparar_migracion_continuar_cirugia.py` OK · informe escrito
- [ ] **nada despertado** · Monarca avisado con números del resumen
