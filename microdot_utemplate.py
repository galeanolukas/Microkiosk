from utemplate import recompile
from microdot import Microdot, send_file
import os
import gc

# Caché de loaders
_loaders = {
    'main': None,  # Loader para templates principales
    'apps': {}     # Diccionario de loaders por app
}

def init_templates(main_template_dir='templates', loader_class=recompile.Loader):
    """Inicializa el sistema de templates para el directorio principal y apps"""
    global _loaders
    _loaders['main'] = loader_class(None, main_template_dir)

def init_app_templates(app_name, app_template_dir=None):
    """Registra los templates de una app específica"""
    if app_template_dir is None:
        app_template_dir = f"apps/{app_name}/templates"
    
    _loaders['apps'][app_name] = recompile.Loader(None, app_template_dir)

def render_template(template, *args, **kwargs):
    """Renderiza un template del directorio principal"""
    if _loaders['main'] is None:
        init_templates()
    
    try:
        gc.collect()
        return _loaders['main'].load(template)(*args, **kwargs)
    except Exception as e:
        print(f"Error renderizando {template}: {str(e)}")
        return f"<h1>Error en template {template}</h1>"

def render_app_template(app_name, template, *args, **kwargs):
    """Renderiza un template de una app específica"""
    if app_name not in _loaders['apps']:
        init_app_templates(app_name)
    
    try:
        gc.collect()
        return _loaders['apps'][app_name].load(template)(*args, **kwargs)
    
    except Exception as e:
        print(f"Error en app {app_name}, template {template}: {str(e)}")
        return f"<h1>Error en template {template}</h1>"
    
def init_static_routes(app):
    """Decorador para manejar archivos estáticos de forma unificada"""
    @app.route('/static/<path:path>')
    @app.route('/<app_name>/static/<path:path>')
    def serve_static(request, app_name=None, path=None):
        # Determinar si es ruta de app o principal
        if app_name:
            static_dir = f"apps/{app_name}/static"
        else:
            static_dir = "static"
        
        # Mapeo de tipos MIME
        mime_types = {
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.svg': 'image/svg+xml',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2'
        }
        
        ext = os.path.splitext(path)[1].lower()
        content_type = mime_types.get(ext, 'text/plain')
        
        try:
            return send_file(os.path.join(static_dir, path), 
                            content_type=content_type)
        except OSError:
            # Intentar fallback en static principal si es una app
            if app_name:
                try:
                    return send_file(os.path.join('static', path),
                                  content_type=content_type)
                except OSError:
                    pass
            return 'Not found', 404
    
    return app