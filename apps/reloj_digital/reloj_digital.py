from microdot import Microdot, send_file
from microdot_utemplate import render_template_app
import time

reloj_digital = Microdot()

@reloj_digital.route('/')
def index(request):
    return render_template_app("reloj_digital", "reloj_digital.html", appname="Reloj", modo="st")

@reloj_digital.route('/time')
def get_time(request):
    current_time = time.localtime()
    return {
        'hour': current_time[3],
        'minute': current_time[4],
        'second': current_time[5]
    }

