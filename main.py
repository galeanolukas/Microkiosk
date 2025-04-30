import uasyncio as asyncio
from microdot import Microdot, Response, redirect, send_file
#from microdot_utemplate import render_template
from tinydb import TinyDB, Query
import bt_manager
import network
import json
import machine, os, gc, sys, re
import tarfile
from config_manager import read_config, update_config
from apps_manager import install_apps
from microdot_utemplate import init_templates, render_template
import socket
import micropython

micropython.alloc_emergency_exception_buf(100)

app = Microdot()
Response.default_content_type = 'text/html'

db = TinyDB('users.json')
users = db.table('users')
User = Query()

# Crear usuario admin por defecto si no existe
if not users.contains(User.username == 'admin'):
    users.insert({'username': 'admin', 'password': 'admin'})

# Cargar Configuracion guardada
config = read_config()
lista_apps = config["apps"]

def protect_server(func):
    def wrapper(request):
        try:
            return func(request)
        except OSError as e:
            if e.errno in [113, 104]:  # ECONNABORTED/ECONNRESET
                print(f"Conexión interrumpida: {request.path}")
                return Response("", status=204)
            raise
    return wrapper

@app.route('/debug/memoria')
def debug_memoria(request):
    import gc
    gc.collect()
    return {
        'mem_libre': gc.mem_free(),
        'cache_templates': len(template_cache)
    }

def get_mem():
    s = os.statvfs('//')
    mem = s[0] * s[3]
    return mem / 1048576

#Decorador para sessiones
def login_required(f):
    def wrapper(request, *args, **kwargs):
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

def scan_wifi():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active():
        wlan.active(True)
    return [net[0].decode('utf-8') for net in wlan.scan()]

@app.route('/bt/scan', methods=["POST"])
def scan_devices(request):
    config = read_config()
    bt_device = bt_manager.iniciar(config["bt"])
    bt_manager.escanear(bt_device, 3000)
    return redirect("/bt")

@app.route('/config/save-css', methods=['POST'])
def save_css(request):
    css_type = request.args.get('type')  # 'theme' o 'icons'
    if css_type not in ['theme', 'icons']:
        return 'Tipo inválido', 400
    
    try:
        # Sobrescribe el archivo correspondiente
        with open(f'static/default_{css_type}.css', 'w') as f:
            f.write(request.body.decode())
        return 'CSS actualizado', 200
    except Exception as e:
        return f'Error: {str(e)}', 500

def temas_disponibles():
    temas = []
    try:
        with open('static/default_theme.css', 'r') as f:
            contenido = f.read()
            
            # Dividir por "body." y luego extraer el nombre
            partes = contenido.split('body.')
            for parte in partes[1:]:  # Ignorar la primera parte
                if '-theme {' in parte:
                    tema = parte.split('-theme {')[0]
                    if tema not in temas:
                        temas.append(tema)
    
    except Exception as e:
        print("Error leyendo temas:", e)
    return temas

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
            
    return render_template('login.html', error=error,
                           appname="LOGIN",
                           modo=config["wifi"]["modo"],
                           tema=config["config"]["theme"])
    
@app.route('/home')
#@login_required
def home(request):
    board = sys.platform
    memoria = get_mem()
    mem_perc = memoria * 4 / 100
    return render_template('home.html',
                            titulo="MICROKIOSK",
                            modo=config["wifi"]["modo"],
                            tema=config["config"]["theme"],
                            appname="HOME",
                            apps=lista_apps,
                            mem=memoria,
                            mem_perc=mem_perc,
                            user=User.username,
                            board=board.upper()
                           )

@app.route('/sobre')
def sobre(request):
    return render_template('sobre.html',
                           appname="SOBRE",
                           titulo="SOBRE",
                           modo=config["wifi"]["modo"],
                           tema=config["config"]["theme"])


    
@app.route('/static/<path:path>')
def static(request, path):
    if '..' in path:
        # directory traversal is not allowed
        return 'Not found', 404
    
@app.route('/static/<path:path>')
def serve_main_static(request, path):
    """Sirve archivos estáticos del directorio principal"""
    # Mapeo de extensiones a tipos MIME
    mime_map = {
        'css': 'text/css',
        'js': 'text/javascript',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'ico': 'image/x-icon'
    }
    
    ext = path.split('.')[-1].lower()
    content_type = mime_map.get(ext, 'text/plain')
    print(content_type)
    return send_file(f'static/{path}', content_type=content_type)
    
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
                with tarfile.open(temp_path, "r:r") as tar:
                    tar.extractall("apps/")
                    app_name = tar.getnames()[0].split('/')[0]
            else:
                return render_template('appmanager.html',
                                       titulo="APPMANAGER",
                                       appname="APPS MANAGER",
                                       modo=config["wifi"]["modo"],
                                       apps=config["apps"],
                                       msj="Archivo no soportado. Solo .tar",
                                       tema=config["config"]["theme"])

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
                return render_template('global', 'appmanager.html',
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
                           modo=config["wifi"]["modo"],
                           tema=config["config"]["theme"])

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
                           titulo="CONFIGURACIÓN BLUETOOTH",
                           tema=config["config"]["theme"])

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
        "appname": "WIFI MANAGER",
        "tema": config["config"]["theme"]
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
            return redirect('/wifi')

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
        if request.form.get('debug') == 'on':
            new_debug = "True"
        else:
            new_debug = "False"
            
        new_port = int(request.form.get('port'))
        new_theme = request.form.get('theme')

        # Comprobamos si hay cambios que requieren reinicio
        requiere_reinicio = (
            config['config']['debug'] != new_debug or
            config['config']['port'] != new_port
        )

        update_config("config", "debug", new_debug)
        update_config("config", "port", new_port)
        update_config("config", "theme", new_theme)

        if requiere_reinicio:
            return render_template('restarting.html',
                                   appname="CONFIGURACION",
                                   modo=config["wifi"]["modo"],
                                   tema=config["config"]["theme"])

        return redirect('/config')

    return render_template('config.html',
                           port=config['config']['port'],
                           theme=config["config"]["theme"],
                           debug=config['config']['debug'],
                           appname="CONFIGURACION",
                           modo=config["wifi"]["modo"],
                           tema=config["config"]["theme"],
                           temas=temas_disponibles())


if __name__ == '__main__':
    #Carga la config del Sistema
    config = read_config()
    #Instala las apps cargadas
    app = install_apps(app)
    #Ejecuta el servidor del framework
    app.run(port=config["config"]["port"],
            debug=eval(config["config"]["debug"]))
            