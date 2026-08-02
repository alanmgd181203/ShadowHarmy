# CHECKPOINT — Kaiser: índice absoluto + sesgo estructural

**Estado:** dirección Monarca 2026-08-02 · **no cableado fino aún** (doctrina)  
**Relaciona:** [`20_DOCTRINA_KAISER.md`](20_DOCTRINA_KAISER.md) §1 · [`CHECKPOINT_TUSK_BOVEDA_MNT.md`](CHECKPOINT_TUSK_BOVEDA_MNT.md)  
**Código hoy:** Tank inyecta `indexPrice`; matriz `spot/perp/inverse_vs_index`; digest `sesgo_estructural`; **backfill** al arranque de Kaiser: lineal+spot+inverso vs índice (bases pentiverso/trinidad + MNT). Smoke: `validar_kaiser_sesgo_smoke.py` · `validar_kaiser_backfill_sesgo_smoke.py`.

**Refuerzo Jess (`a1f2e7e`):** sesgo **vivo** ya no exige solo líder VERDE — si el semáforo está ROJO por latencia, lee del **nodo más fresco** (mismo espíritu que la visión de Tank). Validado en ritual ojos México: bases × 3 mares con clima vivo tras calentamiento.

Más pares metaverso: **después**.

---

## Qué selló el Monarca (dirección)

1. **Referencia absoluta** = **índice Bybit** (`indexPrice`) por base (LTC, MNT, ETH…).  
   - No es un par que operas; es el norte del mapa.  
   - Bybit lo publica; el ejército ya lo ve (Bridge → Tank).

2. **Kaiser** mide en plazos (día / corto / mediano / largo) el sesgo de cada mar vs índice y publica etiqueta **cero estructural** + clima vivo (normal / tenso / anomalía).

3. Convención signed: `(precio − index) / index × 100` — positivo = caro vs índice.

4. **No** es oportunidad el gap eterno; oportunidad = salir del cero.

---

## Qué NO está sellado aún

- Umbrales numéricos exactos por activo.  
- Fórmula mediana vs media; pesos de plazos.  
- Ley dura “bloquear disparo si spread ≤ cero” vs solo aviso.  
- Sello de capital de bóveda Tusk condicionado a “clima normal” (idea conversada; **no** ley firmada aquí).  
- Referencia interna del ejército (entrada del short, etc.) — ancla de **misión**, no sustituto del índice.

---

## Por qué importa (bóveda + pentiverso)

Sin cero estructural, el ejército trata el gap eterno (inverso unos centavos abajo, spot un poco arriba) como “descuento” o “bóveda inflada” → goteo de centavos / decisiones sesgadas.  
Con índice + sesgo Kaiser: cada general mide contra el **norte** y contra su **clima normal**.

---

## Trabajo futuro (código)

| Paso | Qué | Estado |
|------|-----|--------|
| A | Tag `sesgo_estructural` en digest | ✅ 3.8.P5 |
| B | Plazos + muestras + **backfill** lineal/spot/inverso | ✅ |
| B2 | Sesgo vivo con Tank ROJO → nodo más fresco | ✅ Jess `a1f2e7e` |
| C | Panel Cascada mostrar índice + sesgos | pendiente |
| D | Frecuencia/ETA + puerta Igris usan cero estructural | ✅ 2026-08-02 (`MANTO_CERO_ESTRUCTURAL`) |
| E | Informe Monarca números vivos | script ✅ · tabla completa = correr en Jess |
| F | Backfill metaverso / Spot All | después |

**Manos / trading:** este checkpoint **no** autoriza órdenes.

---

## Nota al agente

No inventar “L1–L9” como Códice firmado. Aquí solo: **índice = absoluto**; **Kaiser = sesgos vs índice**. El resto requiere nuevo sello Monarca.
