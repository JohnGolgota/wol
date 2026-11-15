#!/usr/bin/env bash
# Habilita Wake-on-LAN de forma persistente en un equipo Linux (el GMKtec K12 u otro).
# Ejecutar en la máquina DESTINO (la que se quiere encender), con sudo.
set -euo pipefail

IFACE="${1:-}"
if [ -z "$IFACE" ]; then
    # Interfaz con ruta por defecto a la LAN.
    IFACE="$(ip route get 192.168.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')"
fi
if [ -z "$IFACE" ]; then
    echo "No se pudo detectar la interfaz. Pásala como argumento: $0 eth0" >&2
    exit 1
fi

echo "Interfaz detectada: $IFACE"
MAC="$(cat /sys/class/net/$IFACE/address 2>/dev/null || true)"
echo "MAC: $MAC"

# Comprobar soporte WOL
if command -v ethtool >/dev/null 2>&1; then
    ethtool "$IFACE" | grep -i "Wake-on" || true
fi

# Activar ahora
ethtool -s "$IFACE" wol g
echo "WOL activado ahora (modo 'g' = magic packet)."

# Servicio systemd para persistir tras reinicios
SERVICE=/etc/systemd/system/wol-enable.service
cat > "$SERVICE" <<EOF
[Unit]
Description=Enable Wake-on-LAN on $IFACE
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/sbin/ethtool -s $IFACE wol g
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Ajustar ruta de ethtool si no está en /usr/sbin
ETHTOOL_PATH="$(command -v ethtool)"
sed -i "s#^ExecStart=.*#ExecStart=$ETHTOOL_PATH -s $IFACE wol g#" "$SERVICE"

systemctl daemon-reload
systemctl enable --now wol-enable.service
echo "Servicio wol-enable.service habilitado."

echo
echo "Verifica con: ethtool $IFACE | grep -i wake"
echo "MAC para enviar WOL desde otro equipo: $MAC"
