#!/usr/bin/env bash
# Instala el comando `wol` en este equipo y (opcionalmente) en servl.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

install_local() {
    mkdir -p "$HOME/.local/bin" "$HOME/.config/wol"
    cp "$DIR/wol.py" "$HOME/.local/bin/wol"
    chmod +x "$HOME/.local/bin/wol"
    if [ ! -f "$HOME/.config/wol/targets.json" ]; then
        cp "$DIR/targets.example.json" "$HOME/.config/wol/targets.json"
        echo "Creado $HOME/.config/wol/targets.json (edita la MAC del GMKtec)."
    fi
    echo "Instalado localmente: ~/.local/bin/wol"
}

install_servl() {
    echo "Instalando en servl..."
    ssh servl 'mkdir -p ~/.local/bin ~/.config/wol'
    scp "$DIR/wol.py" servl:~/.local/bin/wol
    ssh servl 'chmod +x ~/.local/bin/wol'
    if ! ssh servl 'test -f ~/.config/wol/targets.json'; then
        scp "$DIR/targets.example.json" servl:~/.config/wol/targets.json
        echo "Creado targets.json en servl (edita la MAC)."
    fi
    echo "Instalado en servl: ~/.local/bin/wol"
}

install_local
if [ "${1:-}" = "--with-servl" ]; then
    install_servl
fi

echo
echo "Asegúrate de que ~/.local/bin esté en PATH."
