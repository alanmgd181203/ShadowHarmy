import { useEffect, useState } from "react";

const ESTADO_URL = "/data/estado_vivo.json";

/** Foto viva del ejército. Null hasta el primer pulso. */
export function useEstadoVivo(intervalMs = 3000) {
  const [snap, setSnap] = useState(null);

  useEffect(() => {
    let alive = true;
    async function load() {
      try {
        const res = await fetch(`${ESTADO_URL}?t=${Date.now()}`, { cache: "no-store" });
        if (!res.ok) return;
        const data = await res.json();
        if (alive) setSnap(data);
      } catch {
        /* silencio */
      }
    }
    load();
    const t = setInterval(load, intervalMs);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, [intervalMs]);

  return snap;
}
