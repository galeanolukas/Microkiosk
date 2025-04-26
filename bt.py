import bluetooth
import time
import uasyncio as asyncio

devices_found = []

async def iniciar(bt_config):
    bt = bluetooth.BLE()
    if bt_config.get("active", "False") == "True":
        bt.active(True)

    nombre = bt_config.get("name", "Microkiosk_BT")
    modo = bt_config.get("mode", "peripheral")

    if modo == "peripheral":
        bt.config(gap_name=nombre)
        print("Bluetooth en modo Peripheral activado")
        # Aquí podrías iniciar servicios GATT
        
    elif modo == "central":
        print("Bluetooth en modo Central activado")
        # Aquí podrías escanear dispositivos
        
    elif modo == "both":
        bt.config(gap_name=nombre)
        print("Bluetooth en modo Both activado")
        # Agregar comportamiento mixto

    return bt

def bt_irq(event, data):
    devices_found = []
    if event == bluetooth._IRQ_SCAN_RESULT:
        addr_type, addr, adv_type, rssi, adv_data = data
        mac = ':'.join('{:02X}'.format(b) for b in addr)
        name = bluetooth.decode_name(adv_data) or "Unknown"
        devices_found.append({"name": name, "mac": mac})

def escanear(blue, seg=3000):
    global devices_found
    try:
        blue.active(True)
        # Escanear (5 segundos por ejemplo)
        blue.irq(bt_irq)  # ← ahora sí escucha eventos
        blue.scan(seg)   # Escanea por 3 segundos
        time.sleep(1)   # Esperar a que termine
        blue.active(False)

    except Exception as e:
        print(f"Error al escanear BT: {e}")
        return devices_found
    