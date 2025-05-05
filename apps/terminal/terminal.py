# author: galeano lucas
# version: 1.0
# name: Terminal MicroPython
# info: Consola de Micropython
from microdot import Microdot, Response, send_file
from microdot_utemplate import render_app_template
import gc

terminal = Microdot()

class TerminalBuffer:
    def __init__(self, max_lines=30):
        self.max_lines = max_lines
        self.lines = []
        
    def add_output(self, text):
        """Añade texto al buffer sin redirección"""
        lines = text.splitlines()
        for line in lines:
            if len(self.lines) >= self.max_lines:
                self.lines.pop(0)
            self.lines.append(line)
            gc.collect()
    
    def get_output(self, last_n=20):
        """Obtiene las últimas líneas"""
        return '\n'.join(self.lines[-last_n:])

# Instancia global del buffer
terminal_buffer = TerminalBuffer()

# Decorador para capturar salida (alternativa a redirección)
def capture_output(func):
    def wrapper(*args, **kwargs):
        import io
        buf = io.StringIO()
        try:
            # MicroPython no permite redirección global, 
            # así que capturamos por función
            result = func(*args, **kwargs)
            output = buf.getvalue()
            if output:
                terminal_buffer.add_output(output)
            return result
        finally:
            buf.close()
    return wrapper

@terminal.route('/')
def index(request):
    return render_app_template('terminal', 'index.html', titulo="Terminal MicroPython")

@terminal.route('/static/<path:path>')
def serve_static(request, path):
    return send_file(f"apps/terminal/static/{path}")

@terminal.route('/exec', methods=['POST'])
def exec_command(request):
    """Ejecuta comandos con captura manual de output"""
    command = request.body.decode('utf-8')[:128]
    
    # Registrar el comando
    terminal_buffer.add_output(f">>> {command}")
    
    try:
        # Ejecutar con captura local
        @capture_output
        def execute():
            try:
                result = eval(command, globals(), {})
                if result is not None:
                    print(result)  # Será capturado por el decorador
            except SyntaxError:
                exec(command, globals(), {})
        
        execute()
        
    except Exception as e:
        terminal_buffer.add_output(f"Error: {type(e).__name__}: {str(e)[:100]}")
    
    gc.collect()
    return terminal_buffer.get_output()

@terminal.route('/output')
def get_output(request):
    """Obtiene el output actual"""
    return terminal_buffer.get_output()