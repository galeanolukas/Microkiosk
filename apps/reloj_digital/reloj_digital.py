# author: galeano lucas
# version: 1.0
# name: Reloj Digital
# info: Reloj en tiempo real
from microdot import Microdot, send_file
from microkiosck_utemplate import render_app_template, load_base_templates
import time

reloj_digital = Microdot()

@reloj_digital.route('/')
def index(request):
    return render_app_template("reloj_digital",
                               "reloj_digital.html",
                               appname="Reloj",
                               modo="st",
                               tpl=load_base_templates())

@reloj_digital.route('/time')
def get_time(request):
    current_time = time.localtime()
    return {
        'hour': current_time[3],
        'minute': current_time[4],
        'second': current_time[5]
    }

