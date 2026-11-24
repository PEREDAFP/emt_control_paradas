# Consulta de Autobuses EMT Madrid (CLI)

Aplicación de línea de comandos (CLI) desarrollada íntegramente con la biblioteca estándar de Python (`stdlib`) y secuencias de escape ANSI para consultar información en tiempo real de los autobuses de la Empresa Municipal de Transportes (EMT) de Madrid.

> **Nota para `opencode`:** Este documento define la arquitectura, restricciones técnicas y requisitos funcionales del proyecto. Implementa el código respetando estrictamente la restricción de cero dependencias externas.

---

## Requisitos Técnicos y Restricciones

1. **Lenguaje:** Python 3.8+.
2. **Cero dependencias externas (`stdlib` únicamente):**
   - **Peticiones HTTP:** Utilizar `urllib.request`, `urllib.error` y `urllib.parse`. No usar `requests` ni `httpx`.
   - **Serialización:** Utilizar `json`.
   - **Variables de entorno:** Implementar un cargador propio en Python puro que lea el archivo `.env` ubicado en el directorio raíz del proyecto y cargue las variables en `os.environ`. No usar `python-dotenv`.
   - **Interfaz de terminal (UI):** Utilizar códigos de escape ANSI estándar (`\033[...`) para colores, negritas, limpieza de pantalla, tablas alineadas y cursor. No usar `curses`, `rich` ni `colorama`.
3. **API Base URL:** `https://openapi.emtmadrid.es/`

---

## Configuración y Variables de Entorno

Las credenciales de acceso a MobilityLabs / OpenAPI EMT Madrid se almacenarán en un archivo `.env` en el directorio raíz del proyecto.

Crear un archivo `.env.example` como plantilla y añadir `.env` al `.gitignore`:

```env
EMT_EMAIL=tu_usuario_o_email@ejemplo.com
EMT_PASSWORD=tu_contraseña
```

### Autenticación con la API
- Al iniciar la aplicación (o bajo demanda al realizar la primera consulta), se debe autenticar contra la API para obtener el `accessToken`:
  - **Endpoint de login:** `GET https://openapi.emtmadrid.es/v1/mobilitylabs/user/login/`
  - **Cabeceras (`Headers`):**
    - `email`: valor de `EMT_EMAIL`
    - `password`: valor de `EMT_PASSWORD`
  - **Respuesta:** Extraer `data[0]["accessToken"]` e incluirlo en las cabeceras (`{"accessToken": token}`) de las siguientes peticiones.

---

## Estructura del Menú Interactivo

La interfaz de terminal debe mostrar una cabecera estilizada con ANSI, indicar si hay una línea activa seleccionada en el estado de la sesión y presentar exactamente las siguientes opciones:

```text
1.- Seleccionar Línea
2.- Mostrar paradas
3.- Tiempo de espera en parada
4.- Líneas que llegan a una parada
0.- Salir
```

### Comportamiento esperado por opción

1. **`1.- Seleccionar Línea`**
   - Solicita al usuario el número o identificador de línea (ej. `27`, `146`, `C1`, `N12`).
   - Valida que la línea exista consultando el endpoint de líneas de EMT (`GET /v1/transport/busemtmad/lines/{lineId}/info/` o `/v2/transport/busemtmad/lines/info/`).
   - Guarda la línea seleccionada (junto con su origen/destino) en el estado activo de la sesión y muestra confirmación visual en verde.

2. **`2.- Mostrar paradas`**
   - Muestra el listado ordenado de paradas de la línea previamente seleccionada en la opción 1 (permitiendo elegir sentido ida/vuelta o mostrando ambos itinerarios).
   - Si el usuario aún no ha seleccionado una línea en la opción 1, solicitarla en ese momento o redirigir a la selección de línea.
   - Endpoint de referencia: `GET /v1/transport/busemtmad/lines/{lineId}/stops/{direction}/` (donde `direction` suele ser `1` o `2`).
   - Mostrar código de parada, nombre y dirección/ubicación formateados en columnas limpias.

3. **`3.- Tiempo de espera en parada`**
   - Solicita al usuario el código numérico de la parada (ej. `70`, `1890`).
   - Consulta los tiempos estimados de llegada en tiempo real:
     - Endpoint de referencia: `POST /v2/transport/busemtmad/stops/{stopId}/arrives/`
     - Payload JSON: `{"cultureInfo": "ES", "Text_StopRequired_YN": "Y", "Text_EstimationsRequired_YN": "Y", "Text_IncidencesRequired_YN": "N"}`
   - Muestra los próximos autobuses formateados con colores ANSI (ej. verde para `< 3 min` / en parada, amarillo para tiempos medios, cian para número de línea y destino).

4. **`4.- Líneas que llegan a una parada`**
   - Solicita al usuario el código numérico de la parada.
   - Consulta el detalle de la parada:
     - Endpoint de referencia: `GET /v1/transport/busemtmad/stops/{stopId}/detail/`
   - Lista todas las líneas que operan en dicha parada junto con su cabecera de origen/destino y sentido.

---

## Estructura Sugerida del Proyecto

```text
emt-madrid-cli/
├── .env                  # Variables de entorno (ignorado en git)
├── .env.example          # Plantilla de variables de entorno
├── .gitignore
├── README.md             # Este archivo de especificaciones
└── src/
    ├── __init__.py
    ├── main.py           # Punto de entrada y bucle principal del menú
    ├── config.py         # Lector propio de .env usando stdlib
    ├── api_client.py     # Cliente HTTP con urllib, gestión de token y endpoints EMT
    └── ui.py             # Utilidades ANSI (colores, tablas, limpieza de pantalla, prompts)
```

---

## Manejo de Errores y UX en Terminal

- **Credenciales faltantes o inválidas:** Mostrar un mensaje claro en rojo ANSI indicando cómo configurar el archivo `.env` sin volcar trazas de excepción crudas al usuario.
- **Errores de red / HTTP:** Capturar `urllib.error.HTTPError` y `urllib.error.URLError`, informando del código de estado y permitiendo volver al menú principal.
- **Navegación fluida:** Tras mostrar los resultados de cualquiera de las opciones, esperar a que el usuario pulse `Enter` antes de limpiar la pantalla y redibujar el menú principal.