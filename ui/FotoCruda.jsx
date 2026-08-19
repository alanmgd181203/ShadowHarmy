import { useState } from "react";

/**
 * Foto cruda del ejército — todo lo que emite la foto viva.
 * Caótico a propósito: luego se esconde o se ordena.
 */
export default function FotoCruda({ titulo = "Foto cruda", data, defaultOpen = false }) {
  const [open, setOpen] = useState(Boolean(defaultOpen));
  const vacio = data == null || (typeof data === "object" && !Array.isArray(data) && Object.keys(data).length === 0);

  return (
    <section className="rounded-2xl border border-dashed border-white/15 bg-[#0d0f14]/80">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2.5 text-left active:scale-[0.99]"
      >
        <span className="text-[10px] uppercase tracking-[0.2em] text-white/40">{titulo}</span>
        <span className="text-[10px] text-white/30">{open ? "ocultar" : vacio ? "00" : "ver todo"}</span>
      </button>
      {open ? (
        <div className="px-3 pb-3 max-h-[70vh] overflow-auto">
          {vacio ? (
            <p className="text-sm text-white/35">Sin foto — dormido o aún no late.</p>
          ) : (
            <Nodo valor={data} profundidad={0} />
          )}
        </div>
      ) : null}
    </section>
  );
}

function Nodo({ valor, profundidad }) {
  if (valor == null) {
    return <span className="text-white/30">00</span>;
  }
  if (typeof valor === "boolean") {
    return <span className="text-emerald-400/90">{valor ? "sí" : "no"}</span>;
  }
  if (typeof valor === "number") {
    if (!Number.isFinite(valor)) return <span className="text-white/30">00</span>;
    return <span className="tabular-nums text-white/85">{String(valor)}</span>;
  }
  if (typeof valor === "string") {
    const s = valor.length > 240 ? `${valor.slice(0, 240)}…` : valor;
    return <span className="text-white/75 break-all">{s || "—"}</span>;
  }
  if (Array.isArray(valor)) {
    if (valor.length === 0) return <span className="text-white/30">[]</span>;
    const recorte = valor.slice(0, 48);
    return (
      <div className="pl-2 border-l border-white/10 space-y-1">
        {recorte.map((item, i) => (
          <details key={i} className="text-[11px]" open={profundidad < 1}>
            <summary className="cursor-pointer text-white/40">[{i}]</summary>
            <div className="pl-2 py-0.5">
              <Nodo valor={item} profundidad={profundidad + 1} />
            </div>
          </details>
        ))}
        {valor.length > recorte.length ? (
          <p className="text-[10px] text-white/30">+{valor.length - recorte.length} más</p>
        ) : null}
      </div>
    );
  }
  if (typeof valor === "object") {
    const keys = Object.keys(valor);
    if (keys.length === 0) return <span className="text-white/30">{"{}"}</span>;
    if (profundidad > 8) return <span className="text-white/30">…</span>;
    return (
      <div className="space-y-0.5">
        {keys.map((k) => (
          <details key={k} className="text-[11px]" open={profundidad < 1}>
            <summary className="cursor-pointer text-cyan-400/70">{k}</summary>
            <div className="pl-2 py-0.5">
              <Nodo valor={valor[k]} profundidad={profundidad + 1} />
            </div>
          </details>
        ))}
      </div>
    );
  }
  return <span className="text-white/50">{String(valor)}</span>;
}
