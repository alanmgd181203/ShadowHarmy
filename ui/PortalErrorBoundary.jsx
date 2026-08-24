import { Component } from "react";

/** Si un portal/lienzo revienta, no apaga toda la Cascada (pantalla negra). */
export default class PortalErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch() {
    /* silencio — el Monarca ve el aviso abajo */
  }

  render() {
    if (this.state.error) {
      const msg = String(this.state.error?.message || this.state.error || "error");
      return (
        <div className="absolute inset-0 z-50 flex flex-col items-center justify-center gap-4 bg-[#0a0c10] text-white p-6">
          <p className="text-sm text-rose-300/90 text-center max-w-xs">
            El portal tropezó. La Cascada sigue viva.
          </p>
          <p className="text-[10px] text-white/40 text-center max-w-sm break-words">{msg}</p>
          <button
            type="button"
            className="px-4 py-2 rounded-lg border border-white/20 text-xs uppercase tracking-widest"
            onClick={() => {
              this.setState({ error: null });
              this.props.onClose?.();
            }}
          >
            Volver
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
