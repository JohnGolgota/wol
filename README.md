# Wake-on-LAN (WOL) para GMKtec NucBox K12

Guía para **habilitar** Wake-on-LAN en un GMKtec NucBox K12 y **usarlo** desde otro
mini PC de tu red local (el "servidor local" con alias SSH `servl`, 192.168.1.2).

> "Wake-on-LAN" (WOL) permite encender un equipo apagado (o en suspensión) enviando
> un "magic packet" UDP a su dirección MAC a través de la red local.

---

## 1. Conceptos rápidos

- El WOL se envía a la **MAC** del equipo destino, no a su IP.
- Solo funciona por **Ethernet cableado** (la Wi-Fi del K12 no suele despertar con WOL).
- El equipo que envía el paquete (aquí `servl`) debe estar en la **misma subred** (192.168.1.0/24)
  o el router debe reenviar el broadcast.
- El K12 debe estar apagado o en suspensión, con la NIC recibiendo energía en standby
  (por eso se desactiva ErP/EuP y el "Fast Startup" de Windows).

---

## 1.1 ¿Es obligatorio el cable Ethernet?

**Para Wake-on-LAN clásico (magic packet), sí: debe ir por Ethernet cableado.**
La Wi-Fi del K12 (WoWLAN) casi nunca despierta el equipo desde apagado (S5) de forma
fiable; depende del driver y del BIOS, y en los mini PCs GMKtec no suele funcionar
al 100 %. Por eso la guía asume cable.

Si no tienes cable del router al salón, estas son las alternativas reales:

1. **Powerline / PLC** (recomendado): adaptadores que llevan la red por la instalación
   eléctrica. Pones uno junto al router y otro en el salón; el K12 se conecta por cable
   al adaptador del salón. Latencia suficiente para WOL y para uso normal.
2. **Nodo mesh con puerto LAN**: un satélite Wi-Fi mesh en el salón con un puerto
   Ethernet; el K12 se conecta por cable a ese nodo. El WOL viaja por la red local
   (el broadcast llega al router y se reenvía).
3. **Auto Power On + enchufe inteligente** (no es WOL, pero enciende el equipo):
   en el BIOS del K12 pon **Advanced → AC Power Lost Policy → Power On**, y controla
   un smart plug del salón desde `servl` (o desde Home Assistant). Cortar y restaurar
   la corriente enciende el K12. Ojo: apaga bien el equipo antes de cortar corriente
   para no corromper datos; y el arranque es más lento.
4. **Extender cable temporalmente**: para la configuración inicial (anotar MAC,
   probar) basta con conectar el K12 por cable al router una vez; después puedes
   volver a Wi-Fi para el uso diario y usar la opción 1/2/3 para encenderlo.

> Si al final te quedas solo con Wi-Fi, prueba WoWLAN con `ethtool <iface> wol g` sobre
> la interfaz Wi-Fi; si el driver lo soporta, el mismo `wol.py` funcionará. Pero no
> cuentes con ello.

---

## 2. Habilitar WOL en el GMKtec NucBox K12

### 2.1 BIOS (hardware)

Según el manual del K12:

1. Apaga el K12 y vuelve a encenderlo. Durante el arranque pulsa **ESC** repetidamente
   hasta entrar al BIOS (Aptio Setup - AMI).
2. Con la flecha derecha (→) ve a la pestaña **Advanced**.
3. Baja con (↓) hasta **Wake On Lan**.
4. Pulsa **Enter**, selecciona **Enabled** (por defecto ya viene Enabled) y confirma.
5. (Opcional) En **Advanced → AC Power Lost Policy** pon **Power On** si quieres que
   arranque solo al recuperar la corriente.
6. Ve a **Save & Exit** → **Save Changes and Exit**.

> Si en tu BIOS aparece una opción **ErP / EuP 2013** o "EuP 2014", déjala en
> **Disabled**, porque ErP corta la energía a la NIC en standby y rompe el WOL.

### 2.2 Obtener la MAC del K12 (la necesitarás para enviar WOL)

Enciende el K12 normalmente y, en el sistema operativo:

- **Windows (PowerShell):**
  ```powershell
  getmac /v
  # o
  ipconfig /all
  ```
- **Linux:**
  ```bash
  ip link show
  # o
  cat /sys/class/net/enp*/address
  ```

Anota la MAC de la interfaz Ethernet (formato `AA:BB:CC:DD:EE:FF`). Es la que pondrás
en `targets.json`.

### 2.3 Configuración del sistema operativo

#### Si el K12 tiene Windows 11 (configuración por defecto de GMKtec)

1. Abre **Administrador de dispositivos** → **Adaptadores de red** → tu tarjeta Ethernet
   (Realtek/Intel) → **Propiedades**.
2. Pestaña **Administración de energía**:
   - Marca "Permitir que este dispositivo reactive el equipo".
   - Marca "Permitir solo un paquete mágico para reactivar el equipo" (recomendado).
3. Pestaña **Opciones avanzadas**:
   - "Wake on Magic Packet" → **Enabled**.
   - "Wake on Pattern Match" → Disabled (opcional).
4. Desactiva el **Inicio rápido** de Windows (rompe WOL):
   - Panel de control → Opciones de energía → "Elegir lo que hacen los botones de
     inicio/apagado" → "Cambiar la configuración no disponible actualmente" →
     desmarca "Activar inicio rápido".
5. (Opcional) En el plan de energía, desactiva la suspensión selectiva del USB/Ethernet.

#### Si el K12 tiene Linux

Ejecuta en el K12 (con sudo):

```bash
sudo ./enable-wol-linux.sh
# o indicando la interfaz:
sudo ./enable-wol-linux.sh enp3s0
```

El script:
- activa `ethtool -s <iface> wol g`,
- crea y habilita el servicio `wol-enable.service` para que persista tras reinicios.

Verifica:

```bash
ethtool enp3s0 | grep -i wake
# debe mostrar: Wake-on: g
```

---

## 3. Usarlo desde `servl` (el mini PC controlador)

`servl` es tu servidor local (192.168.1.2). Desde él enviarás el magic packet al K12.

### 3.1 Instalar la herramienta en servl

En este equipo (try1), desde la carpeta del proyecto:

```bash
cd ~/Proyectos/wol
./install.sh --with-servl
```

Esto copia `wol.py` como `~/.local/bin/wol` en servl y crea
`~/.config/wol/targets.json` (si no existía).

### 3.2 Configurar la MAC del GMKtec

Edita en servl (o copia desde aquí) `~/.config/wol/targets.json`:

```json
{
  "gmktec": {
    "mac": "AA:BB:CC:DD:EE:FF",
    "broadcast": "192.168.1.255",
    "port": 9
  }
}
```

Sustituye `AA:BB:CC:DD:EE:FF` por la MAC real del K12.

Asegúrate de que `~/.local/bin` esté en el PATH de servl (añade a `~/.bashrc` o
`~/.config/fish/config.fish` si hace falta):

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### 3.3 Encender el K12

Desde este equipo:

```bash
# Enviar el paquete desde servl (recomendado, porque servl está siempre encendido)
./wake-gmktec.sh servl

# O directamente por SSH:
ssh servl 'wol --target gmktec'

# O enviar desde este equipo:
./wake-gmktec.sh
```

Opciones útiles del script:

```bash
wol --mac AA:BB:CC:DD:EE:FF
wol --mac AA:BB:CC:DD:EE:FF --broadcast 255.255.255.255 --port 7
wol --target gmktec --count 5
wol --list
```

### 3.4 Verificar que arrancó

```bash
# Espera ~10-30 s y luego:
ping -c 4 192.168.1.13   # (IP del K12 si la conoces)
ssh serv@192.168.1.13     # o el alias que tengas
```

> Ajusta la IP del K12 según tu red. Si no la conoces, revisa el router/ARP
> (`ip neigh`) o el DHCP del router.

---

## 4. Crear un alias cómodo (opcional)

En `~/.bashrc` o `~/.config/fish/config.fish` de este equipo:

```bash
alias wol-gmktec='ssh servl "wol --target gmktec"'
```

Y en servl, si quieres encenderlo por nombre:

```bash
alias gmktec-on='wol --target gmktec'
```

---

## 5. Solución de problemas (troubleshooting)

| Síntoma | Causa probable | Solución |
|---|---|---|
| No enciende nunca | WOL desactivado en BIOS | Revisa BIOS → Advanced → Wake On Lan = Enabled |
| No enciende nunca | ErP/EuP corta energía a la NIC | Desactiva ErP en BIOS |
| No enciende desde Windows | Inicio rápido activo | Desactiva Fast Startup |
| No enciende desde Windows | "Permitir que este dispositivo reactive..." desmarcado | Marcar en Administrador de dispositivos |
| Enciende a veces | NIC pierde config tras reinicio (Linux) | Usa `enable-wol-linux.sh` (servicio systemd) |
| `ethtool` muestra `Wake-on: d` | Modo desactivado | `ethtool -s eth0 wol g` |
| El paquete no llega | Broadcast bloqueado por router/VLAN | Envía a la IP de broadcast correcta (192.168.1.255) o a la IP del K12 si el router hace proxy-ARP; prueba también 255.255.255.255 |
| Solo funciona en suspensión, no apagado | Windows apagado con Fast Startup / S5 no soportado por driver | Desactiva Fast Startup; actualiza driver |
| WOL por Wi-Fi no funciona | La Wi-Fi del K12 no soporta WOL en S5 | Usa Ethernet cableado |
| MAC incorrecta | Copiaste la MAC de la Wi-Fi | Usa la MAC de la interfaz Ethernet |
| El K12 enciende pero no responde a SSH | Tarda en arrancar o IP cambió | Espera 30-60 s; revisa DHCP/router |

Comandos de diagnóstico:

```bash
# En servl: ver si el paquete sale (requiere tcpdump)
sudo tcpdump -i enp3s0f0 -n udp port 9 or port 7

# En servl: enviar y ver resultado
wol --target gmktec --count 5

# En K12 (Linux): estado WOL
ethtool eth0 | grep -i wake

# Ver vecinos ARP (para confirmar MAC/IP)
ip neigh
```

---

## 6. Seguridad

- El magic packet **no tiene autenticación**: cualquiera en tu LAN puede encender el K12.
- No expongas el puerto WOL a Internet; envíalo siempre desde `servl` (dentro de la LAN)
  vía SSH.
- Si quieres más control, deja `wol` solo en servl y accede a servl por SSH (ya
  configurado con clave `id_homelab`).

---

## 7. Archivos del proyecto

- `wol.py` — envía el magic packet (CLI).
- `enable-wol-linux.sh` — habilita WOL persistente en Linux (destino).
- `install.sh` — instala `wol` localmente y en servl (`--with-servl`).
- `wake-gmktec.sh` — atajo para encender el K12 (`servl` o local).
- `targets.example.json` — plantilla de destinos.
- `systemd/wol-enable.service.example` — servicio systemd de ejemplo.

---

## 8. Flujo típico de uso diario

```bash
# 1) (Una sola vez) configura BIOS + OS del K12 y anota su MAC en targets.json.
# 2) Desde cualquier equipo:
ssh servl 'wol --target gmktec'
# 3) Espera ~20 s y conecta:
ssh serv@192.168.1.13
```
