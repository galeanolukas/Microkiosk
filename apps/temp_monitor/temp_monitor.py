# author: [Tu nombre]
# version: 1.0
# name: Monitor de Temperatura
# info: Muestra la temperatura ambiente usando sensor de la ESP32
from microdot import Microdot, send_file
from microkiosk_utemplate import render_app_template
import time
from machine import Pin, ADC

sensor_temp = ADC(Pin(34))  # ADC en pin 34
sensor_temp.atten(ADC.ATTN_11DB)  # Rango completo 0-3.3v

temp_monitor = Microdot()

def read_temperature():
    """Función para leer la temperatura (simulada o real)"""
    raw = sensor_temp.read()
    temp = (raw / 4095) * 3.3 * 100  # Conversión simple (ajustar según tu sensor)

    # Simulación mientras pruebas:
    temp = 25.3 + (time.time() % 10) * 0.1  # Temperatura fluctuante para pruebas

    return round(temp, 1)

@temp_monitor.route('/')
def index(request):
    current_temp = read_temperature()
    return render_app_template("temp_monitor", "temp_monitor.html",
                             appname="Temperatura",
                             modo="st",
                             tema="light",
                             temperatura=current_temp
                            )

@temp_monitor.route('/temp')
def get_temp(request):
    """Endpoint para obtener la temperatura actual (AJAX)"""
    current_temp = read_temperature()
    return {'temperature': current_temp}

@temp_monitor.route('/static/<path:path>')
def static(request, path):
    """Servir archivos estáticos"""
    return send_file(f'static/{path}')
