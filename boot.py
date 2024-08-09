# boot.py -- run on boot-up
import network
import json
import socket
from machine import Pin
import usocket
import utime
import os

# Replace the following with your WIFI Credentials
lrgb_ob = Pin(2, Pin.OUT, value=0)
lrgb_ob.off()

#SSID = "AP_ESP32"
#SSI_PASSWORD = "G4l34n0L"

config = None
with open("config.json") as f:
    config = json.load(f)
    
def blink(on=True):
    if on:
        utime.sleep(0.5)
        lrgb_ob.on()
        utime.sleep(0.5)
        lrgb_ob.off()
    else:
        lrgb_ob.on()

def do_ap_connect(SSID, SSI_PASSWORD):
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=SSID, password=SSI_PASSWORD, authmode=network.AUTH_WPA_WPA2_PSK)

    while not ap.isconnected():
        blink()

    print('Conexion exitosa!')
    blink(False)
    print(ap.ifconfig())

def do_connect(SSID, SSI_PASSWORD):
    import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('Conectando a la Red...')
        sta_if.active(True)
        sta_if.connect(SSID, SSI_PASSWORD)
        blink()
        while not sta_if.isconnected():
            blink(False)
            pass
    print('Conectado! Red Wifi:', sta_if.ifconfig())
    

if config["wifi"]["modo"] == "ap":
    do_ap_connect(config["wifi"]["ssid"], config["wifi"]["password"])
else:
    do_connect(config["wifi"]["ssid"], config["wifi"]["password"])

