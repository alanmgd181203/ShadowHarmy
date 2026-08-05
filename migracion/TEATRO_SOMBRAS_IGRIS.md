# Teatro de sombras Igris — laboratorio (pre-manos)

**Estado:** óptica Tank cableada · **NO es 4.0.3 live** · **NO soltado** overnight hasta orden GO del Monarca.  
**Fecha artefacto:** 2026-08-04

## Qué es (lenguaje del ejército)

Imagina **un solo Tank** mirando el campo (misma cinta de precios) y, detrás, **cuatro sombras de Igris de papel**. Cada sombra lleva una marcha distinta:

- **Táctico** — umbral alto (paciencia: fees completos)
- **Marcha forzada** — umbral medio (½ fees · puede apretar)
- **Asalto** — umbral cero · entra a mercado sin esperar el edge
- **Personalizado** — umbral calibrado a un tiempo T (solo en memoria del teatro)

Las cuatro **ven lo mismo**. Lo que cambia es **cuándo muerden** y **con qué calidad de entrada** (spread al fill, distancia al mid, espera, fees vs notional, avance de lote de papel).

No pelean por la bóveda real de Tusk. Cada sombra tiene contadores etiquetados (`sombra_tactico`, …). Campo limpio al GO. Igris / Greed / Beru reales **hibernados**; manos OFF; bóveda manos OFF.

## Qué NO es

- **No** es 4.0.3 (Igris live hasta manto 100%).
- **No** son cuatro `arise` completos compartiendo la misma bóveda.
- **No** suelta manos reales ni enciende bóveda MNT.
- **No** marca el checklist live como hecho: esto es laboratorio pre-manos.

## Óptica: sintético vs Tank vivo

| Modo | Cuándo | Qué ve |
|------|--------|--------|
| **Sintético** | `--preparar`, o `--go` sin `--optica-tank`, o `--sintetico` | Mercado de juguete (seguro, sin red) |
| **Tank vivo** | `--go --optica-tank` | Un Bridge + un Tank; tickers estrechos; opcional `--con-libros` |

**Política (segura):** GO serio del Monarca **exige** `--optica-tank`. Sin ese flag, el script corre sintético y avisa. Si pides Tank y no conecta, **aborta** (no finge mercado vivo con demo).

Ojos por defecto: **books OFF** (ticker + libro sintético 1-nivel, como `arise_igris_sim`). `--con-libros` enciende orderbooks (más red/RAM).

## Cómo se prepara (sanidad)

```bash
python3 scripts/teatro_sombras_igris.py --preparar
```

Corre en segundos, siempre sintético, sin WS ni caffeinate. Sella `data/logs/teatro_sombras/preparar_sanidad.json`.

## Cómo se suelta (cuando el Monarca diga GO)

**GO serio — óptica Tank** (ejemplo 8 h, pulso cada 5 s):

```bash
python3 scripts/teatro_sombras_igris.py --go --optica-tank --horas 8 --intervalo 5 --activo ETH
```

Sanity corto (no overnight):

```bash
python3 scripts/teatro_sombras_igris.py --go --optica-tank --segundos 15 --intervalo 5 --activo ETH
```

Demo sin mercado:

```bash
python3 scripts/teatro_sombras_igris.py --go --sintetico --segundos 30
```

Con deadline:

```bash
python3 scripts/teatro_sombras_igris.py --go --optica-tank --durar-hasta 2026-08-05T08:00:00 --activo ETH
```

Guardián (relanzable, **OFF por defecto** — exige confirmación; **propaga `--optica-tank`**):

```bash
python3 scripts/vigilar_teatro_sombras.py --confirmar-go --horas 8
```

Demo vía guardián: añade `--sintetico`. Sin `--confirmar-go` el guardián **no lanza** nada.

## Dónde mirar el botín

Carpeta: `data/logs/teatro_sombras/` (gitignored junto con `data/logs/`)

- `preparar_sanidad.json` — sello de sanidad
- `resumen_parcial.json` / `resumen_monarca.json` — comparación de las 4 sombras (`meta.optica` = `tank` | `sintetico`)
- `decisiones.jsonl` — cada pulso (quién mordió / esperó)
- `heartbeat.json` — pulso vivo

## Código

- Núcleo: `core/teatro_sombras.py` (`vision_desde_tank`, `correr_hasta` / `correr_hasta_async`)
- Entrada: `scripts/teatro_sombras_igris.py`
- Guardián: `scripts/vigilar_teatro_sombras.py`

Doctrina de marchas: `core/pase_director.py` · ritmo: `core/marcha_ritmo_lote.py`.

## Riesgos (ojos)

- **Keys:** la óptica del teatro usa WS **público** (sin session privada). Keys Bybit no hacen falta para mirar; si faltan, igual puede ver tickers.
- **Skew / books OFF:** sin muros reales, el edge se estima con ticker + medio spread artificial — útil para comparar marchas, no para medir profundidad de libro.
- **Apagado:** al salir (fin de batida, Ctrl+C o abort de calentamiento) se cancelan las tareas WS — no dejar zombie.

## Siguiente del camino

1. Monarca ordena **GO** con `--optica-tank` (o via guardián `--confirmar-go`).
2. Tras la batida: leer `resumen_monarca.json` — qué marcha mordió mejor (no solo conteo).
3. Solo después, con orden explícita: **4.0.3** Igris live (manos reales).
