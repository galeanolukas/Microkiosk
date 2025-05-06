import bluetooth
import time
# GLOBAL: Lista de dispositivos encontrados
devices_found = []

_IRQ_SCAN_RESULT = 5
_IRQ_SCAN_DONE = 6

# Iniciar Bluetooth
def iniciar(bt_config):
    global bt
    bt = bluetooth.BLE()

    if bt_config.get("active", "False") == "True":
        bt.active(True)

    nombre = bt_config.get("name", "Microkiosk_BT")
    modo = bt_config.get("mode", "peripheral")

    if modo in ("peripheral", "both"):
        bt.config(gap_name=nombre)
        print("Bluetooth en modo Peripheral activado")
        
    if modo in ("central", "both"):
        print("Bluetooth en modo Central activado")
        
    return bt

# Función para decodificar el nombre (simple)
def decode_name(adv_data):
    # Busca el campo 0x09 (Complete Local Name)
    i = 0
    while i + 1 < len(adv_data):
        length = adv_data[i]
        if length == 0:
            break
        type = adv_data[i + 1]
        if type == 0x09:
            return adv_data[i + 2:i + 1 + length].decode('utf-8')
        i += 1 + length
    return "Unknown"

# Handler de eventos
def bt_irq(event, data):
    global devices_found
    if event == _IRQ_SCAN_RESULT:
        addr_type, addr, adv_type, rssi, adv_data = data
        mac = ':'.join('{:02X}'.format(b) for b in addr)
        name = decode_name(adv_data)
        devices_found.append({"name": name, "mac": mac})

# Función para escanear dispositivos
def escanear(bt, segundos=3000):
    global devices_found
    devices_found = []

    try:
        if not bt.active():
            bt.active(True)

        bt.irq(bt_irq)  # Captura eventos de descubrimiento
        bt.gap_scan(segundos)   # Escanear
        
        print(f"Escaneando dispositivos Bluetooth por {segundos/1000} segundos...")
        time.sleep(segundos/1000 + 0.5)  # Esperar el tiempo de escaneo más un pequeño margen
        
        bt.gap_scan(None)  # Detener escaneo (mejor práctica)
        
    except Exception as e:
        print(f"Error al escanear Bluetooth: {e}")

    finally:
        try:
            bt.irq(None)  # Limpiar IRQ
        except:
            pass

    print(devices_found)
    return devices_found
