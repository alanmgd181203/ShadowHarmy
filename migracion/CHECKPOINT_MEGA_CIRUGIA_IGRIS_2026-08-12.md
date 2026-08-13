# Checkpoint — Mega-cirugía Igris v1 (2026-08-12)

**Manos:** no implica Arise live. Arise quieto al operar.

## Qué se soldó

1. **Sueño + misiones** — `core/igris_mision.py`; latido del Escudo ejecuta misión y duerme; sargento auto arma sembrar/engordar desde pase.
2. **Solo Asalto** — `IGRIS_SOLO_ASALTO`; personalizado → asalto en normalizar/perfil.
3. **Bocado asimétrico** — `core/igris_bocado.py`; no empate Market de \$ (`IGRIS_DUAL_SALVAVIDAS_EMPATE=false`); emergencia pierna muerta ON.
4. **§A sin piloto** — `IGRIS_OXIGENO_PILOTO=false`; poda auto off.
5. **Reducir** — cableado + espera confirmación (no ejecuta bisturí de campo aún).
6. **MNT** — Santo engordable. Short “bóveda” **no** se reconstruye (mega-cirugía ejército: no es saco).
7. **Telemetría** — `igris.mision` en estado_vivo (Bellion).
8. **Doctrina 21** + sellos + dudas finas.
9. **Altar / pulso UI** (post-inventario) — solo Asalto en el altar; personalizado legado → asalto; portal Manto lee sueño·misión para DORMIDO/DESPIERTO.
10. **Injerto Jess (útil solo, 2026-08-12)** — piernas L/S en el pase; bóveda `MNTPERP/MNTUSDC`; canal/logs por Santo; ETH en ojos; proxy WS directo; sin escapes LIVE_TESTNET. **No** cura Market de espejo (→ DUDAS V13–V15).

## Dudas (no asumidas)

Ver `DUDAS_CIRUGIAS_MENORES_2026-08-12.md` (V1…V15 · C1…C5). V6 bóveda USDC = **cerrada**.

## Smoke

`python scripts/validar_igris_sueno_mision_smoke.py` → OK

## Siguiente

Cirugías finas Igris (dudas V*) · Tank ojos si hace falta · Beru después.