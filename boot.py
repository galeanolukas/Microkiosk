# boot.py -- run on boot-up
import network
import json
import socket
from machine import Pin
import usocket
import utime
import time
import os, sys
from config_manager import init_config, read_config
print(os.uname())
print(sys.version)
# Replace the following with your WIFI Credentials
lrgb_ob = Pin(2, Pin.OUT, value=0)
lrgb_ob.off()
#Iniciar la configuracion
init_config()
#Leer la configuracion
config = read_config()

def blink():
    lrgb_ob.on()
    utime.sleep(0.3)
    lrgb_ob.off()
    utime.sleep(0.3)

def do_ap_connect(SSID, SSI_PASSWORD):
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=SSID, password=SSI_PASSWORD, authmode=network.AUTH_WPA_WPA2_PSK)

    print('Esperando conexión...')
    connected = False

    while True:
        stations = ap.status('stations')  # [(mac,), ...] o [(mac, ip)]
        if stations:
            connected = True
            break
        blink()  # Función para parpadear LED mientras no hay conexión
        time.sleep(0.5)

    lrgb_ob.on()  # LED fijo
    print('Conexión exitosa en modo AP')
    print('Clientes conectados:', stations)
    print('Configuración IP:', ap.ifconfig())

def do_connect(SSID, SSI_PASSWORD, wifi_config):
    import network
    sta_if = network.WLAN(network.STA_IF)
    # IP fija si se configuró
    if eval(wifi_config["ip_fija"]):
        ip = "192.168.1.98"
        gateway = "192.168.1.1"
        subnet = "255.255.255.0"
        dns = "0.0.0.0"
        sta_if.ifconfig((ip, gateway, subnet, dns))
        
    if not sta_if.isconnected():
        print('Conectando a la Red...')
        sta_if.active(True)
        sta_if.connect(SSID, SSI_PASSWORD)
        
        # Bucle de conexión con parpadeo
        while not sta_if.isconnected():
            blink()  # Titila

    print('¡Conectado a WiFi!')
    lrgb_ob.on()  # Fijo cuando conecta
    print('IP:', sta_if.ifconfig())
    
    
if config["wifi"].get("modo", "") == "ap":
    do_ap_connect(config["wifi"]["ssid"], config["wifi"]["password"])
else:
    do_connect(config["wifi"]["ssid"], config["wifi"]["password"], config["wifi"])