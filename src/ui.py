"""Utilidades de interfaz de terminal con códigos de escape ANSI (stdlib).

Proporciona colores, limpieza de pantalla, cabecera, menú, prompts y tablas
alineadas para la CLI de EMT Madrid. No usa curses, rich ni colorama.
"""

from typing import Dict, List, Optional

# Secuencias de escape ANSI
_RESET = "\033[0m"
_NEGRITA = "\033[1m"
_ROJO = "\033[31m"
_VERDE = "\033[32m"
_AMARILLO = "\033[33m"
_AZUL = "\033[34m"
_CIAN = "\033[36m"
_BLANCO = "\033[37m"

# Colores con estilo negrita para mayor legibilidad en terminal
_NEGRITA_ROJO = "\033[1;31m"
_NEGRITA_VERDE = "\033[1;32m"
_NEGRITA_AMARILLO = "\033[1;33m"
_NEGRITA_CIAN = "\033[1;36m"
_NEGRITA_BLANCO = "\033[1;37m"


def _color(codigo: str, texto: str) -> str:
    """Envuelve texto con un código de color ANSI y reseteo."""
    return f"{codigo}{texto}{_RESET}"


def rojo(texto: str) -> str:
    return _color(_ROJO, texto)


def verde(texto: str) -> str:
    return _color(_VERDE, texto)


def amarillo(texto: str) -> str:
    return _color(_AMARILLO, texto)


def cian(texto: str) -> str:
    return _color(_CIAN, texto)


def negrita(texto: str) -> str:
    return _color(_NEGRITA, texto)


def limpiar_pantalla() -> None:
    """Limpia la pantalla y coloca el cursor en la esquina superior izquierda."""
    print("\033[2J\033[H", end="")


def pausa(mensaje: str = "Pulsa Enter para continuar...") -> None:
    """Espera a que el usuario pulse Enter antes de seguir."""
    try:
        input(f"\n{_color(_CIAN, mensaje)}")
    except (EOFError, KeyboardInterrupt):
        print()


def ok(texto: str) -> str:
    """Mensaje de confirmación en verde."""
    return f"{_NEGRITA_VERDE}✔{_RESET} {texto}"


def error(texto: str) -> str:
    """Mensaje de error en rojo."""
    return f"{_NEGRITA_ROJO}✖{_RESET} {texto}"


def info(texto: str) -> str:
    """Mensaje informativo en azul."""
    return f"{_NEGRITA_BLANCO}ℹ{_RESET} {texto}"


def encabezado(titulo: str, linea_activa: Optional[Dict[str, str]] = None) -> None:
    """Dibuja la cabecera estilizada de la aplicación.

    Muestra el título, un separador y, si hay una línea seleccionada en la
    sesión, su estado activo.
    """
    ancho = 70
    print(_color(_NEGRITA_CIAN, "═" * ancho))
    print(_color(_NEGRITA_BLANCO, f"  {titulo}"))
    print(_color(_NEGRITA_CIAN, "═" * ancho))

    if linea_activa:
        lid = linea_activa.get("id", "-")
        origen = linea_activa.get("origen", "-")
        destino = linea_activa.get("destino", "-")
        print(
            f"  Línea activa: {negrita(lid)}  |  "
            f"{origen} → {destino}"
        )
    else:
        print(f"  Línea activa: {rojo('ninguna')}")
    print(_color(_NEGRITA_CIAN, "═" * ancho))


def mostrar_menu() -> None:
    """Imprime el menú principal con las opciones del README."""
    print()
    print(_color(_AMARILLO, "  1.- Seleccionar Línea"))
    print(_color(_AMARILLO, "  2.- Mostrar paradas"))
    print(_color(_AMARILLO, "  3.- Tiempo de espera en parada"))
    print(_color(_AMARILLO, "  4.- Líneas que llegan a una parada"))
    print(_color(_ROJO, "  0.- Salir"))
    print()


def prompt(texto: str) -> str:
    """Solicita una entrada al usuario con un prompt en cian."""
    try:
        return input(f"{_color(_CIAN, texto)} ")
    except (EOFError, KeyboardInterrupt):
        print()
        return "0"


def tabla(encabezados: List[str], filas: List[List[str]], ancho_total: int = 70) -> None:
    """Imprime una tabla simple con columnas alineadas a la izquierda.

    Cada fila es una lista de strings ya recortados para ajustarse a su
    columna. La última columna se deja sin rellenar para aprovechar el ancho.
    """
    if not filas:
        print("  (sin resultados)")
        return

    anchos = [len(e) for e in encabezados]
    for fila in filas:
        for i, celda in enumerate(fila):
            if i < len(anchos):
                anchos[i] = max(anchos[i], len(celda))

    def _linea(celdas: List[str]) -> str:
        partes = []
        for i, celda in enumerate(celdas):
            if i < len(celdas) - 1:
                partes.append(celda.ljust(anchos[i]))
            else:
                partes.append(celda)
        return "  " + " | ".join(partes)

    print(_linea(encabezados))
    print("  " + "-" * min(ancho_total, sum(anchos) + 3 * (len(encabezados) - 1) + 2))
    for fila in filas:
        print(_linea(fila))


def formatear_minutos(minutos: Optional[int]) -> str:
    """Devuelve el tiempo de espera con color según el valor."""
    if minutos is None:
        return color_texto("—", _AMARILLO)
    if minutos <= 0:
        return color_texto("en parada", _VERDE)
    if minutos < 3:
        return color_texto(f"{minutos} min", _VERDE)
    if minutos < 10:
        return color_texto(f"{minutos} min", _AMARILLO)
    return color_texto(f"{minutos} min", _BLANCO)


def color_texto(texto: str, codigo: str) -> str:
    return _color(codigo, texto)
