from microdot import Microdot, Response
from microkiosck_utemplate import render_template

home_app = Microdot()
Response.default_content_type = 'text/html'

@home_app.route('/')
def test(request, methods=["GET"]):
    return "Hola Mundo Prueba!!!"
