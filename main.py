from microdot import Microdot, Response, redirect, send_file
from microdot_utemplate import render_template
from tinydb import TinyDB, Query
import bluetooth
import network
import json
import machine, os, gc, sys
from config_manager import *

app = Microdot()
Response.default_content_type = 'text/html'
# app.mount('/static', Static('./static'))

# Inicializa Bluetooth
#ble = bluetooth.BLE()
#ble.active(True)

db = TinyDB('users.json')
users = db.table('users')
User = Query()

# Crear usuario admin por defecto si no existe
if not users.contains(User.username == 'admin'):
    users.insert({'username': 'admin', 'password': 'admin'})

# Cargar Configuracion guardada
config = read_config()
lista_apps = config["apps"]

#Decorador para sessiones
def login_required(f):
    async def wrapper(request, *args, **kwargs):
        user_cookie = request.cookies.get('user')

        if not user_cookie:
            return redirect('/')

        user = db.get(User.username == user_cookie)
        if not user:
            return redirect('/')

        # Pasamos el usuario al handler
        request.user = user
        return await f(request, *args, **kwargs)

    return wrapper

def get_mem():
    s = os.statvfs('//')
    mem = s[0] * s[3]
    return mem / 1048576

def scan_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    networks = wlan.scan()  # Devuelve una lista de tuplas con la información de las redes
    wifi_list = []
    for net in networks:
        wifi_list.append(net[0].decode('utf-8'))
        
    return wifi_list
    
# Cargar las apps desde el dir apps
def load_apps():
    for app_dir in os.listdir("apps"):
        if app_dir == "__init__.py" or app_dir == "__pycache__":
            pass
        else:
            lista_apps.append(app_dir)
            
    update_config(None, "apps", lista_apps)
    return lista_apps

#funcion que importa los modulos instalados
def import_modules(path):
    with open(f'apps/{path}/{path}.py') as f:
        code = f.read()
        exec(code)
        
#instala los modulos dentro de la app principal
def install_apps(current_app):

    if lista_apps:
        for app_name in lista_apps:
            import_modules(app_name)
            if app_name in dir():
                sub_app = eval(app_name)
                current_app.mount(sub_app, url_prefix=f'/{app_name}')
            
    return current_app

#### Vistas por defecto del SO ###
@app.route('/', methods=['GET', 'POST'])
async def login(request):
    error = None
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')
        user = users.get((User.username == username) & (User.password == password))
        
        if user:
            response = redirect('/home')
            response.set_cookie('user', username)
            return response
        
        else:
            error = 'Usuario o contraseña incorrectos'
    return render_template('login.html', error=error, appname="LOGIN")

@app.route('/home')
#@login_required
async def home(request):
    board = sys.platform
    memoria = get_mem()
    mem_perc = memoria * 4 / 100
    return render_template('home.html',
                            titulo="MICROKIOSK",
                            modo=config["wifi"]["modo"],
                            appname="HOME",
                            apps=lista_apps,
                            mem=memoria,
                            mem_perc=mem_perc,
                            user=User.username,
                            board=board.upper())

@app.route('/sobre')
async def sobre(request):
    return render_template('sobre.html', appname="SOBRE", titulo="SOBRE", modo=config["wifi"]["modo"])

@app.route('/static/<path:path>')
async def static(request, path):
    if '..' in path:
        # directory traversal is not allowed
        return 'Not found', 404
    
    return send_file('static/' + path)

@app.route('/appm', methods=["GET", "POST"])
async def app_manager(request):
    if request.method == "POST":
        pass
    
    return render_template('appmanager.html',
                           titulo="APPMANAGER",
                           appname="APPS MANAGER",
                           modo=config["wifi"]["modo"],
                           apps=config["apps"])

@app.route('/reiniciar', methods=["GET", "POST"])
async def reiniciar(request):
    if request.method == "POST":
        import time
        time.sleep(1)
        machine.reset()
        return redirect('/')
    
    return render_template('reboot.html',
                           appname="APAGAR PLACA",
                           titulo="",
                           modo=config["wifi"]["modo"])

@app.route('/bt', methods=["GET", "POST"])
async def blue(request):    
    if request.nethod == "POST":
        pass
        
    return render_template('bt.html',
                           bt=config["bt"]["active"],
                           modo=config["wifi"]["modo"],
                           appname="BLUETOOTH MANAGER", titulo="")
        
@app.route('/wifi', methods=["GET", "POST"])
async def wifi_conect(request):
    redes = scan_wifi()
    config_wifi = {}
    context = {"name":None,
                   "msj":None,
                   "ssid":None,
                   "password":None,
                   "modo":"ap",
                   "ip":"",
                   "appname":"WIFI MANAGER"}
            
    if request.method == "POST":
        ssid = request.form['essid']
        psk = request.form['password']
        modo = request.form['modo']
        ip = request.form['ip']
        if ssid and psk:
            config_wifi["wifi"]["ssid"] = ssid
            config_wifi["wifi"]["password"] = psk
            config_wifi["wifi"]["modo"] = modo
            config_wifi["wifi"]["ip"] = ip
            update_config(None, "wifi", config_wifi)
            machine.reset()
            return redirect('/')
        else:
            context['msj'] = "Debe completar los campos!"
            return redirect('/')

    if config:
        context["ssid"] = config["wifi"]["ssid"]
        context["password"] = config["wifi"]["password"]
        context["modo"] = config["wifi"]["modo"]
    else:
        pass
                
    return render_template('wifi.html', ssid=context["ssid"],
                            titulo="WIFI CONECTAR",
                            msj=context["msj"],
                            appname=context["appname"],
                            modo=context["modo"],
                            password=context["password"],
                            redes=redes,
                            ip=context["ip"])

@app.route('/logout')
async def logout(request):
    response = redirect('/login')
    response.delete_cookie('user')
    return response

@app.route('/config', methods=['GET', 'POST'])
async def config_view(request):
    config = read_config()

    if request.method == 'POST':
        new_debug = request.form.get('debug') == 'on'
        new_port = int(request.form.get('port'))
        new_theme = request.form.get('theme')

        # Comprobamos si hay cambios que requieren reinicio
        requiere_reinicio = (
            config['config']['debug'] != new_debug or
            config['config']['port'] != new_port
        )

        update_config("config", new_debug)
        update_config("config", new_port)
        update_config("config", new_theme)

        if requiere_reinicio:
            return render_template('restarting.html')

        return redirect('/config')

    return render_template('config.html',
                           port=config['config']['port'],
                           theme=config["config"]["theme"],
                           debug=config['config']['debug'],
                           appname="CONFIGURACION",
                           modo=config["wifi"]["modo"])


if __name__ == '__main__':
    config = read_config()
    app = install_apps(app)
    app.run(port=config["config"]["port"],
            debug=eval(config["config"]["debug"]))