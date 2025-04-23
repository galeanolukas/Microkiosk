# Micro SO para Microcontroladores en MicroPython

## 🧠 Objetivo del Proyecto

Este proyecto tiene como objetivo desarrollar un sistema operativo ligero (**Micro SO**) para microcontroladores como el ESP32, Raspberry Pi Pico y otros similares, utilizando **MicroPython** como lenguaje de programación principal. 

El sistema está orientado a funcionar como un entorno tipo **kiosk**, permitiendo la instalación y gestión de aplicaciones a través de una API tipo servidor.

---

## 🚀 Características Principales

- ### Lenguaje y Entorno:
  - **MicroPython**: Adaptación de Python para hardware de recursos limitados.
  - **Microdot**: Microframework inspirado en Flask para operaciones de red y API.

- ### Compatibilidad con Hardware:
  - **ESP32, Raspberry Pi Pico, entre otros**: Compatible con los microcontroladores más utilizados en proyectos de IoT.

- ### Sistema Kiosk:
  - Interfaz simplificada para el usuario, controlando completamente el entorno.

- ### Gestión de Aplicaciones:
  - **Instalación y actualización vía API**.
  - **Repositorio centralizado** para apps compatibles.

- ### Seguridad y Control:
  - **Aislamiento de aplicaciones**: Cada app corre en su propio entorno.
  - **Actualizaciones seguras** con verificación de integridad.

---

## 🧩 Aplicaciones del Proyecto

Este Micro SO es ideal para:

- **IoT y dispositivos inteligentes**.
- **Terminales de autoservicio, kiosks o puntos de venta**.

---

## 🔧 Cómo Crear Aplicaciones para el Micro SO

Cada app compatible con el sistema debe respetar esta estructura:

```
apps/
└── nombre_app/
    ├── nombre_app.py
    ├── templates/
    │   └── index.html
    └── static/
```

### ✅ Reglas:

- El archivo principal debe tener el mismo nombre que la carpeta.  
  Ej: `apps/test_app/test_app.py`

- Ejemplo básico de app:

```python
from microdot import Microdot

test_app = Microdot()

@test_app.route('/')
def index(request):
    return "Hola desde Test App"
```

- Template sugerido para cada app:

```html
{% args titulo, appname, modo %}
<html>
  {% include 'head.html' %}
  <body>
    {% include 'top_bar.html' %}
    <div class="w3-content w3-padding">
        <div class="w3-card-4 w3-margin w3-white">
            <header class="w3-container w3-blue">
                <h1>{{ titulo }}</h1>
            </header>
            <div class="w3-container w3-padding">
                <!-- contenido dinámico -->
            </div>
            <footer class="w3-container w3-blue">
                <h5>{{ appname }} - Modo: {{ modo }}</h5>
            </footer>
        </div>
    </div>
  </body>
</html>
```

- Registro en `config.json` para cargar la app automáticamente:

```json
{
  "apps": ["home_app", "test_app"]
}
```

---

## 🔮 Futuras Expansiones

- Soporte para más hardware y sistemas embebidos.
- Interfaz gráfica ligera para facilitar la interacción del usuario.

---

## 🧪 Créditos

Proyecto desarrollado con ❤️ en MicroPython, utilizando Microdot y W3.CSS.

---

## 📁 Estructura del Proyecto

```
/apps
/config.json
/static
/templates
main.py
```

---

> Este proyecto es una iniciativa experimental para impulsar entornos livianos y seguros en
