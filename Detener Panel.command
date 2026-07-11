#!/bin/bash
ROOT="$(cd "$(dirname "$0")" && pwd)"
bash "$ROOT/scripts/detener_panel.sh"
read -r -p "Pulsa Enter para cerrar..."
