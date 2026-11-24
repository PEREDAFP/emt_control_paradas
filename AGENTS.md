# AGENTS.md

Este repositorio contiene solo la **especificación** (`README.md`) de una CLI de consola para consultar autobuses EMT Madrid. No hay código fuente, tests, CI, lockfile ni `opencode.json`.

## Stack y restricciones (verificadas en README.md)

- **Python 3.8+**, **stdlib únicamente**. Cero dependencias externas.
- No usar `requests`/`httpx` → `urllib.request`, `urllib.error`, `urllib.parse`.
- No usar `python-dotenv` → cargador propio de `.env` con `os`/`os.environ`.
- No usar `curses`/`rich`/`colorama` → escape codes ANSI (`\033[...`).
- API base URL: `https://openapi.emtmadrid.es/`

## Entorno

- Crear `.env` en la raíz del proyecto con `EMT_EMAIL` y `EMT_PASSWORD` (no subirlo; ya está en `.gitignore`).
- Plantilla sugerida: `.env.example` con las mismas claves.

## Autenticación con la API

1. `GET https://openapi.emtmadrid.es/v1/mobilitylabs/user/login/` con cabeceras `email` y `password`.
2. Extraer `data[0]["accessToken"]` y enviarlo en cabecera `{"accessToken": token}` en las peticiones siguientes.

## Lo que NO existe aún (no buscar ni inventar)

- No hay entrypoint implementado (README sugiere `src/main.py`, `config.py`, `api_client.py`, `ui.py`, pero es solo una sugerencia, no está creado).
- No hay tests, ni pytest, ni configuración de lint/formatter/typecheck.
- No hay CI ni workflows de GitHub.

## Cuando se implemente

- Respetar estrictamente la restricción de stdlib únicamente del README.
- Manejar `urllib.error.HTTPError` y `URLError` sin mostrar trazas crudas al usuario.
- `.env` ya está ignorado por `.gitignore`; no hacer commit de credenciales.
