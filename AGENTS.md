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
- `src/api_client.py` — `EMTClient` con `login()`, `line_info()`, `line_stops()`, `stop_arrives()`, `stop_detail()`.
- Ejecutar como módulo: `python -m src.api_client` (sin instalar nada).

## Entorno

- `.env` en la raíz con `EMT_EMAIL` y `EMT_PASSWORD` (ya creado localmente).
- `.env` está en `.gitignore`; **no hacer commit de credenciales**.

## Autenticación con la API

1. `GET https://openapi.emtmadrid.es/v1/mobilitylabs/user/login/` con cabeceras `email` y `password`.
2. Extraer `data[0]["accessToken"]` y enviarlo en cabecera `{"accessToken": token}` en las peticiones siguientes.

## Lo que NO existe aún

- No hay `src/main.py` ni `src/ui.py` (menú interactivo pendiente).
- No hay tests, ni pytest, ni configuración de lint/formatter/typecheck.
- No hay CI ni workflows de GitHub.

## Cuando se implemente

- Respetar estrictamente stdlib únicamente.
- Manejar `urllib.error.HTTPError` y `URLError` sin mostrar trazas crudas al usuario.
- No commitear credenciales (`.env` ignorado por `.gitignore`).
