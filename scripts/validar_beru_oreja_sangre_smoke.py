"""Oreja de sangre: precio ya detrás → arma; restore reengancha oreja."""
from __future__ import annotations

from types import SimpleNamespace

from core import beru_rango as br


def _beru(**kw):
    b = SimpleNamespace(
        estado="ACECHANDO",
        direccion="",
        sangre_lado="ARRIBA",
        sangre_adan=100.0,
        oreja_sangre_activa=True,
        es_relevo_cazador=True,
        ultima_hoz_direccion="LONG",
        ultima_hoz_tocada_precio=98.0,
        oz_despliegue_px=98.0,
        oz_adan=0.0,
        red_adan=97.0,
        red_pct=0.0,
        cero_wake=100.0,
        centro_local=100.0,
        ancla_tramo=100.0,
        centro_manto=100.0,
        masa=0.0,
        masa_tramo_usd=0.0,
        engorde_bloqueado=True,
        engorde_cero_oz_px=0.0,
        engorde_ancla_px=0.0,
        engorde_peldaño_offset=0,
        engorde_memoria_peldaños=0,
        engorde_campana_dir="",
        sangre_campana_oz0_px=0.0,
        sangre_campana_dir="",
        rango_escalones_red=0,
        cosechas_continuas=1,
        saco_long_usd=10.0,
        saco_short_usd=0.0,
        altar_revision=0,
        altar_link_id="",
        altar_order_id="",
        altar_order_status="",
        altar_trigger_price=0.0,
        altar_cancel_confirmado=False,
        altar_entrada_disparada=False,
        altar_market_ts=0.0,
        sangre_vista_dentro=True,
        origen_tramo="",
        trail_extremo=0.0,
        oz_pct=0.0,
        llamado_tramo_pct=0.0,
        caza_trail_iniciado=False,
        tramo_precio_activacion=0.0,
        masa_doctrinal_usd=0.0,
    )
    for k, v in kw.items():
        setattr(b, k, v)
    return b


def main() -> None:
    b = _beru()
    assert br.toca_sangre(b, 100.0), "precio en sangre ARRIBA debe tocar"
    assert br.toca_sangre(b, 101.5), "precio ya detrás debe tocar (no solo el cruce)"
    assert not br.toca_sangre(b, 99.0), "debajo de sangre ARRIBA no toca"

    masa = br.armar_tramo_desde_sangre(b, precio=101.5)
    assert masa > 0, masa
    assert str(b.estado).upper() == "CAZANDO", b.estado
    assert str(b.direccion).upper() == "SHORT", b.direccion

    # Restore: oreja + hoz_px desde oz_despliegue
    b2 = _beru(
        oreja_sangre_activa=False,
        es_relevo_cazador=False,
        ultima_hoz_tocada_precio=0.0,
        estado="ACECHANDO",
        direccion="",
        masa=0.0,
    )
    br.restaurar_acecho_post_oz(
        b2,
        cero=100.0,
        red=97.0,
        sangre_lado="ARRIBA",
        ultima_hoz_direccion="LONG",
        oz_despliegue=98.0,
        cosechas=2,
        sangre_sello_px=100.0,
    )
    assert bool(b2.oreja_sangre_activa), "restore debe abrir oreja"
    assert bool(b2.es_relevo_cazador), "restore debe marcar relevo"
    assert float(b2.ultima_hoz_tocada_precio or 0) > 0, "restore debe clavar hoz_px"
    assert br.toca_sangre(b2, 101.0), "tras restore, sangre detrás debe oírse"
    print("OK oreja_sangre_ya_detras")


if __name__ == "__main__":
    main()
