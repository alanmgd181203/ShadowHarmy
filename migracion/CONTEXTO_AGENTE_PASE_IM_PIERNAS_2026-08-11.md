# Contexto agente — peaje IM pierna a pierna + unidades inverso (2026-08-11)

**Audiencia:** Cursor / agente ShadowHarmy  
**Estado:** cambios en working tree (aún no necesariamente pusheados); leer antes de tocar peaje, pase o sizing inverso.  
**Doctrina:** `17_GUIA_MONARCA.md` · checklist `16` ítem Igris/Asalto.

---

## Propósito

Cerrar la mentira del ranking: el pase proyectaba corona Brujo (~\$1451) con equity ~\$1500 porque el peaje usaba **apalancamiento promedio**. Bybit cobra **IM por pierna** (inverse máx + linear máx). Tras Asalto mainnet, el margen real ~97% demostró el hueco.

Trabajo colateral: no tratar `positionValue` de inverse como USD (son coins settle); sellos Monarca forzados OP/ADA; ritual nivelar (bisturí) forjado pero **abortado** (no se recortó manto).

**No reiniciar Arise** salvo orden Monarca (lap apagada).

---

## Cambios por archivo (código / doctrina viva)

### `core/beru_capital.py` — núcleo del parche

- Docstring: peaje/IM **pierna a pierna**; promedio prohibido para ranking; bóveda MNT **fuera** del presupuesto ofensivo (cubre reserva 5%→muro 95%).
- `apalancamiento_manto_promedio`: marcado **LEGADO** (no peaje).
- Nuevo `margen_piernas_para_friccion(asset, friccion)` → `{im_inverse, im_linear, im_total, lev_*, notional_pierna}`.
- `margen_bidireccional_para_friccion` = suma IM inv + IM lin (ya no `2×pierna/avg`).
- Nuevo `delta_peaje_grado` para regenerar deltas del pase.
- `rangos_activo`: expone `lev_inverse`, `lev_linear`, `im_*`; `lev_promedio` solo UI legado.
- `pnl_por_1pct_con_margen`: escala nocional vía IM piernas, no promedio.

Ejemplo contractual: LINK Mariscal → `5000/20 + 5000/50 = 350` IM (antes ~286 con avg 35×).

### `core/pase_director.py`

- `PASE_PASOS` regenerado: `delta_usd` / `acum_usd` desde peaje pierna-a-pierna.
  - Corona Brujo paso 27: **1451 → 1673**
  - Chamán paso 52: **3161 → 3735**
- `cargar_progreso` / `guardar_progreso`: campo `pasos_forzados` + nota; forzados se unen a logrados y **no se desmarcan** en sync aunque `have < need` o pasen potencia.
- `sincronizar_logrados_desde_tusk`: respeta `pasos_forzados` (p.ej. 28, 34, 35).
- Docstring: capital delta = peaje IM dual; bóveda no ofensiva.

### `core/plan_crecimiento.py`

Techos pase alineados:

| Rango     | Antes | Ahora |
|-----------|------:|------:|
| Aspirante | 123   | 143   |
| Aprendiz  | 411   | 478   |
| Brujo     | 1451  | 1673  |
| Chamán    | 3161  | 3735  |

### `core/lote_bybit.py`

- `unidad_lote`: respeta `unidad_min_qty` BD; no aplastar ciego `clave==inverse`.
- `usd_a_qty` / `qty_a_usd`: inverse `usd_contrato` = face USD (qty=USD); **nunca** `qty/precio` como USD.
- `nocional_usd_posicion_bybit`: inverse → `|size|`; linear → positionValue o size×mark.  
  **Por qué:** API `positionValue` en inverso = coins (= size/mark); usarlo como USD inflaba OP/ADA en forenses (~\$6900 fantasma vs size ~\$628 face).

### `core/telemetria_igris.py`

- Inverse: `margen_usd = positionIM × mark` (IM suele venir en coin settle); `_notional` = size (USD face).

### `generales/igris.py`

- Masa / Doctrina B: deja de usar `apalancamiento_manto_promedio`; escala con `margen_piernas_para_friccion`.

### `data/pase_progreso.json`

- Pasos sellados incluyen **28, 34, 35**.
- `pasos_forzados: [28, 34, 35]` — ADA Caballero + OP Caballero/General por orden Monarca (pueden superar potencia / nocional USD face Soldado).
- Nota doctrinal en JSON.

### Scripts

| Archivo | Rol |
|---------|-----|
| `scripts/nivelar_manto_pase.py` | Ritual bisturí `reduceOnly` + dry-run (aprobado forja; **ejecución LIVE abortada** por Monarca) |
| `scripts/validar_beru_capital_smoke.py` | + assert LINK Mariscal IM=350 |
| `scripts/validar_lote_bybit_smoke.py` | + inverse no infla size/precio |
| `scripts/validar_pase_director_smoke.py` | umbrales potencia/lote/meta 1250 |
| `scripts/validar_plan_crecimiento_smoke.py` | techos 143/3735 |

### Fuera de este paquete doctrinal (no documentar como “parche peaje”)

Ruido runtime habitual: `estado_vivo.json`, `historial_hierro.jsonl`, pids, `trinidad_bybit.json`, etc. **No** son el mapa del ranking; no mezclar en el commit doctrinal si se puede evitar.

---

## Números duros post-parche (ofensiva, sin bóveda)

- IM mantos ideales pasos 1–27: **~\$1585**
- Equity ranking corona Brujo (`acum` 27): **\$1673**
- `potencia_n(1500)`: **24** (antes 28)
- Bóveda MNT: Monarca confirma IM del short **dentro** del colchón 5%; **no** sumar al presupuesto ofensivo.

---

## Invariantes para el próximo agente

1. No reintroducir `im = 2×pierna / avg(lev)`.
2. No usar `positionValue` inverso como nocional USD del pase.
3. No borrar `pasos_forzados` al sincronizar.
4. No arrancar Arise / guardián sin orden Monarca.
5. Docs histórico `migracion/PASE_BATALLA_13_SANTOS.md` / `23_PLAN_CRECIMIENTO.md` pueden seguir con \$1451/\$3161 — **código y techos vivos mandan** hasta regenerar esos markdown.

---

## Informe paralelo (Monarca)

Ver: `migracion/INFORME_MONARCA_MAPA_MARGEN_REAL_2026-08-11.md`
