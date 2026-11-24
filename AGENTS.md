# AGENTS.md

Repositorio de la CLI de autobuses EMT Madrid. Especificación funcional en `README.md`.

## Stack y restricciones (del README.md, verificadas)

- **Python 3.8+**, **stdlib únicamente**. Cero dependencias externas.
- No usar `requests`/`httpx` → `urllib.request`, `urllib.error`, `urllib.parse`.
- No usar `python-dotenv` → cargador propio de `.env`.
- No usar `curses`/`rich`/`colorama` → escape codes ANSI (`\033[...`).
- API base URL: `https://openapi.emtmadrid.es/`

## Entrypoints implementados

- `src/config.py` — cargador propio de `.env` (`load_env()`), expone `EMT_EMAIL`, `EMT_PASSWORD`.
- `src/api_client.py` — `EMTClient` con `login()`, `line_info()`, `line_stops()`, `stop_arrives()`, `stop_detail()`, `stop_list()`.
- `src/ui.py` — utilidades de terminal ANSI (colores, tablas, limpieza de pantalla, prompts).
- `src/main.py` — menú interactivo y bucle principal de la aplicación (`App`).
- Ejecutar como módulo: `python -m src.main` (sin instalar nada).

## Entorno

- `.env` en la raíz con `EMT_EMAIL` y `EMT_PASSWORD` (ya creado localmente).
- `.env` está en `.gitignore`; **no hacer commit de credenciales**.

## Autenticación con la API

1. `GET https://openapi.emtmadrid.es/v1/mobilitylabs/user/login/` con cabeceras `email` y `password`.
2. Extraer `data[0]["accessToken"]` y enviarlo en cabecera `{"accessToken": token}` en las peticiones siguientes.

## Lo que NO existe aún

- No hay tests, ni pytest, ni configuración de lint/formatter/typecheck.
- No hay CI ni workflows de GitHub.

## Búsqueda de paradas

- Las opciones "Tiempo de espera en parada" y "Líneas que llegan a una parada" ya no se limitan a la línea seleccionada: aceptan un código numérico directo (ej. `70`, `1890`) o un nombre para buscar entre todas las paradas de EMT (ej. `Sol`).
- `stop_list()` en `api_client.py` (POST `/v1/transport/busemtmad/stops/list/`) obtiene el listado de paradas para soportar la búsqueda por nombre (case-insensitive). Cada parada tiene `node` (código) y `name` (nombre). Si hay varias coincidencias, se muestra una tabla para que el usuario elija.
- `stop_detail()` devuelve las líneas en `data[0].stops[0].dataLine` con campos `line`/`label`, `headerA` (origen), `headerB` (destino), `direction` (sentido).
- `stop_arrives()` devuelve los tiempos en `data[0].Arrive` con `estimateArrive` en segundos (convertido a minutos en la UI).

## Cuando se implemente

- Respetar estrictamente stdlib únicamente.
- Manejar `urllib.error.HTTPError` y `URLError` sin mostrar trazas crudas al usuario.
- No commitear credenciales (`.env` ignorado por `.gitignore`).
