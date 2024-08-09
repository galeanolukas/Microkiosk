from microdot import Microdot, Response
test_app = Microdot()

@test_app.route('/')
def test(request, methods=["GET"]):
    return "Test Hola Mundo!!!"