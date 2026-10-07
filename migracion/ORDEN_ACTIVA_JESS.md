# ORDEN ACTIVA (única)

**Puerta oficial Jess / Cursor México (viejita).**  
Siempre el mismo path: `migracion/ORDEN_ACTIVA_JESS.md`  
Los `PEGAR_JESS_*` son **recetas** (anexo). No son la puerta.

**Actualización 2026-10-07 — Beru arma al tocar (ticket mínimo + lotes OKX)**

---

## 1) Arranque (obligatorio)

```
git fetch origin
git checkout regalo
git pull origin regalo
```

(La cirugía vive en la rama **regalo**.)

Luego **abre solo este archivo** y ejecuta la misión de abajo.

---

## 2) Misión — recargar Beru con altar que nace al tocar

**Qué es:** Beru ya no se queda sordo tras vacío/sangre/red (centavos sin contrato). Al tocar, pone al menos un contrato en OKX y sigue engordando enmendando. Hay que **traer el código** y **reiniciar la flota Beru** (continuar, no desde cero) para que cargue el pergamino nuevo.

**Receta / detalle:** ninguna.

### Comandos exactos (PowerShell, raíz del repo en la viejita)

```
cd C:\Users\lenovo\ShadowHarmy
git fetch origin
git checkout regalo
git pull origin regalo

# Confirmar cirugía en el pergamino
Select-String -Path core\beru_rango_altar.py -Pattern "primer_sello_pide_ticket_min" -SimpleMatch
Select-String -Path core\lote_okx.py -Pattern "minimos\+parametros" -SimpleMatch

# Reiniciar flota Beru con código nuevo (mantiene semilla / --continuar)
C:\Users\lenovo\AppData\Local\Python\pythoncore-3.14-64\python.exe -u tmp_reiniciar_flota_codigo_nuevo.py
```

Espera a que termine el reinicio. Luego pulso corto:

```
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\_pulso_despertar.ps1
```

Opcional — un Santo (NEAR): en el log reciente no debe spam eterno `ALTAR_ESPERA_PISO` tras un ARMAR; si arma, debe haber sello/orden.

---

## 3) Qué NO hacer

- No `--desde-cero` (la flota ya despertó limpia; solo recarga código).
- No apagar Igris / Iron salvo que estén muertos.
- No tocar `.env` ni secretos.
- No volver a `long_short_mode` / piernas.

---

## 4) Qué mirar al terminar

1. `git log -1 --oneline` muestra el commit de ticket mínimo / lotes OKX.
2. Campamentos Beru vivos de nuevo (`_pulso_despertar`).
3. Avisar al Monarca: cuántos Santos relanzados y si el HEAD es el nuevo.

---

## 5) HECHO (Jess / Cursor marca)

- [ ] `git pull origin regalo` hecho
- [ ] Confirmado `primer_sello_pide_ticket_min` en el altar
- [ ] Flota reiniciada con código nuevo
- [ ] Pulso OK · Monarca avisado
