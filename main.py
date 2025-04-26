import uasyncio as asyncio
#from microdot_asyncio import Microdot, Response, redirect, send_file
from microdot import Microdot, Response, redirect, send_file
from microdot_utemplate import render_template
from tinydb import TinyDB, Query
import bt_manager
import network
import json
import machine, os, gc, sys
import tarfile
from config_manager import *

app = Microdot()
Response.default_content_type = 'text/html'
# app.mount('/static', Static('./static'))

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

def verificar_estructura_app(app_folder):
    """Verifica que la app tenga la estructura correcta."""
    # Ruta base de la app
    base_path = f"apps/{app_folder}"

    # Verificar existencia de la carpeta base
    if not os.path.isdir(base_path):
        return False, "No existe la carpeta de la aplicación."

    # Verificar existencia del archivo principal
    principal_py = f"{base_path}/{app_folder}.py"
    if not os.path.isfile(principal_py):
        return False, f"Falta el archivo principal {app_folder}.py."

    # Verificar carpetas templates/ y static/
    templates_path = f"{base_path}/templates"
    static_path = f"{base_path}/static"

    if not os.path.isdir(templates_path):
        return False, "Falta la carpeta templates/"
    if not os.path.isdir(static_path):
        return False, "Falta la carpeta static/"

    return True, "Estructura correcta."

@app.route('/bt/scan', methods=["POST"])
def scan_devices(request):
    config = read_config()
    bt_device = bt_manager.iniciar(config["bt"])
    bt_manager.escanear(bt_device, 3000)
    return redirect("/bt")

#### Vistas por defecto del SO ###
@app.route('/', methods=['GET', 'POST'])
def login(request):
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
    return render_template('login.html', error=error, appname="LOGIN", modo=config["wifi"]["modo"])

@app.route('/home')
#@login_required
def home(request):
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
def sobre(request):
    return render_template('sobre.html', appname="SOBRE", titulo="SOBRE", modo=config["wifi"]["modo"])

@app.route('/static/<path:path>')
def static(request, path):
    if '..' in path:
        # directory traversal is not allowed
        return 'Not found', 404
    
    return send_file('static/' + path)

@app.route('/appm', methods=["GET", "POST"])
def app_manager(request):
    config = read_config()

    if request.method == "POST":
        uploaded_file = request.files.get('file')
        if uploaded_file:
            filename = uploaded_file.filename
            app_name = None

            # Guardar el archivo temporalmente
            temp_path = "/tmp/" + filename
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())

            # Detectar tipo de archivo
            if filename.endswith(".tar"):
                with tarfile.open(temp_path, "r:gz") as tar:
                    tar.extractall("apps/")
                    app_name = tar.getnames()[0].split('/')[0]
            else:
                return render_template('appmanager.html',
                                       titulo="APPMANAGER",
                                       appname="APPS MANAGER",
                                       modo=config["wifi"]["modo"],
                                       apps=config["apps"],
                                       msj="Archivo no soportado. Solo .tar.gz o .zip")

            # Eliminar archivo temporal
            try:
                os.remove(temp_path)
            except:
                pass

            # Verificar estructura antes de registrar
            ok, mensaje = verificar_estructura_app(app_name)
            if not ok:
                # Borrar carpeta si está incompleta
                import shutil
                shutil.rmtree(f"apps/{app_name}")
                return render_template('appmanager.html',
                                       titulo="APPMANAGER",
                                       appname="APPS MANAGER",
                                       modo=config["wifi"]["modo"],
                                       apps=config["apps"],
                                       msj=f"Error en la app: {mensaje}")

            # Registrar y montar app
            if app_name and app_name not in config["apps"]:
                config["apps"].append(app_name)
                update_config(None, "apps", config["apps"])

                global lista_apps
                lista_apps = config["apps"]
                install_apps(app)

            return redirect('/appm')

    return render_template('appmanager.html',
                           titulo="APPMANAGER",
                           appname="APPS MANAGER",
                           modo=config["wifi"]["modo"],
                           apps=config["apps"],
                           msj=None)

@app.route('/reiniciar', methods=["GET", "POST"])
def reiniciar(request):
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
def blue(request):
    config = read_config()
    devices = None
    
    if request.method == "POST":
        bt_status = request.form.get("bt_status")
        bt_name = request.form.get("bt_name") or "Microkiosk_BT"
        bt_mode = request.form.get("bt_mode") or "peripheral"

        config["bt"]["active"] = "True" if bt_status == "on" else "False"
        config["bt"]["name"] = bt_name
        config["bt"]["mode"] = bt_mode

        update_config(None, "bt", config["bt"])

    #Inicia el dispositivo si esta habilitado
    bt_device = bt_manager.iniciar(config["bt"])
    
    return render_template('bt.html',
                           bt=config["bt"]["active"],
                           bt_name=config["bt"].get("name", "Microkiosk_BT"),
                           bt_mode=config["bt"].get("mode", "peripheral"),
                           modo=config["wifi"]["modo"],
                           appname="BLUETOOTH MANAGER",
                           devices=bt_manager.devices_found,
                           titulo="CONFIGURACIÓN BLUETOOTH")

@app.route('/wifi', methods=["GET", "POST"])
def wifi_conect(request):
    redes = scan_wifi()
    config = read_config()
    config_wifi = {"wifi": {}}
    
    context = {
        "name": None,
        "msj": None,
        "ssid": None,
        "password": None,
        "modo": "ap",
        "ip": "",
        "appname": "WIFI MANAGER"
    }

    # Cargar datos actuales de la config
    if config:
        context["ssid"] = config["wifi"]["ssid"]
        context["password"] = config["wifi"]["password"]
        context["modo"] = config["wifi"]["modo"]
        if eval(config["wifi"]["ip_fija"]):
            context["ip"] = config["wifi"]["ip"]

    # Si es GET y hay un ssid seleccionado desde el navegador
    if request.method == "GET":
        ssid = request.args.get('n')
        if ssid:
            context["ssid"] = ssid
            context["password"] = ""  # limpiar password al seleccionar otra red
            context["modo"] = "st"     # cambia automáticamente a modo estación

    if request.method == "POST":
        ssid = request.form['essid']
        psk = request.form['password']
        modo = request.form['modo']
        ip = request.form['ip']

        if ssid and psk:
            update_config("wifi", "ssid", ssid)
            update_config("wifi", "password", psk)
            update_config("wifi", "modo", modo)
            update_config("wifi", "ip", ip)
            utime.sleep(1)
            machine.reset()
        else:
            context['msj'] = "Debe completar SSID y contraseña."
            return render_template('wifi.html', redes=redes, **context)

    return render_template('wifi.html', redes=redes, **context)

@app.route('/logout')
def logout(request):
    response = redirect('/login')
    response.delete_cookie('user')
    return response

@app.route('/config', methods=['GET', 'POST'])
def config_view(request):
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