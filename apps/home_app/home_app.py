from microdot import Microdot, Response
from microdot_utemplate import render_template

home_app = Microdot()
# Response.default_content_type = 'text/html'
# Configura las carpetas de templates y archivos estáticos
app.template_folder = 'templates'
app.static_folder = 'static'


@home_app.route('/prueba')
def prueba(request, methods=["GET"]):
    return render_template('index.html', msj="Hola Mundo!!", appname="")

@home_app.route('/')
def test(request, methods=["GET"]):
    return "Hola Mundo Prueba!!!"
