from microdot import Microdot, Response
from microdot_utemplate import render_template

home_app = Microdot()
Response.default_content_type = 'text/html'


@home_app.route('/')
def prueba(request, methods=["GET"]):
    return render_template('home_app/index.html', msj="Hola Mundo!!")

@home_app.route('/prueba')
def test(request, methods=["GET"]):
    return "Hola Mundo Prueba!!!"