"""Cargador propio de variables de entorno desde .env (stdlib únicamente).

No usa python-dotenv. Lee el archivo .env del directorio raíz del proyecto
y carga las variables en os.environ sin sobrespir variables ya definidas.
"""

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"


def load_env(env_file=ENV_FILE):
    """Carga las variables de un archivo .env en os.environ."""
    path = Path(env_file)
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def get_env(key, default=None):
    """Devuelve el valor de una variable de entorno o default."""
    return os.environ.get(key, default)


# Carga automática al importar el módulo
load_env()

EMT_EMAIL = get_env("EMT_EMAIL")
EMT_PASSWORD = get_env("EMT_PASSWORD")
