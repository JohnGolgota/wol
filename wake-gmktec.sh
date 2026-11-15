#!/usr/bin/env bash
# Atajo para encender el GMKtec K12.
# Uso:
#   ./wake-gmktec.sh            # usa el equipo local (este PC)
#   ./wake-gmktec.sh servl      # envía el paquete desde el mini PC "servl" (recomendado)
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-local}"

if [ "$TARGET" = "servl" ]; then
    echo "Enviando WOL al GMKtec desde servl (192.168.1.2)..."
    ssh servl "python3 - --target gmktec" < "$DIR/wol.py"
else
    echo "Enviando WOL al GMKtec desde este equipo..."
    "$DIR/wol.py" --target gmktec
fi
