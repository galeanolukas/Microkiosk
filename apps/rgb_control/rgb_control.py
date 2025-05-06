# author: galeano lucas
# version: 1.0
# name: RGB Control
# info: Controla leds rgb remotamente
from microdot import Microdot, send_file
from microkiosck_utemplate import render_app_template
from machine import Pin, PWM
import time

red = PWM(Pin(12))
green = PWM(Pin(13))
blue = PWM(Pin(14))
red.freq(1000)
green.freq(1000)
blue.freq(1000)

red.duty_u16(0)
green.duty_u16(0)
blue.duty_u16(0)

rgb_control = Microdot()

@rgb_control.route('/')
def index(request):
    return render_app_template("rgb_control", "rgb_control.html",
                            appname="Control RGB", modo="st")

@rgb_control.route('/static/<path:path>')
def serve_static(request, path):
    return send_file(f"apps/rgb_control/static/{path}")

@rgb_control.route('/set', methods=['POST'])
def set_color(request):
    try:
        data = request.json
        r = int(data.get('r', 0))
        g = int(data.get('g', 0))
        b = int(data.get('b', 0))

        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))

        red.duty_u16(r * 257)    
        green.duty_u16(g * 257)
        blue.duty_u16(b * 257)

        return {'status': 'ok', 'color': {'r': r, 'g': g, 'b': b}}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 400

@rgb_control.route('/preset/<preset>')
def set_preset(request, preset):
    presets = {
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
        'purple': (128, 0, 128),
        'white': (255, 255, 255),
        'off': (0, 0, 0)
    }

    if preset in presets:
        r, g, b = presets[preset]
        red.duty_u16(r * 257)
        green.duty_u16(g * 257)
        blue.duty_u16(b * 257)
        return {'status': 'ok', 'preset': preset}
    else:
        return {'status': 'error', 'message': 'Preset no válido'}, 404
