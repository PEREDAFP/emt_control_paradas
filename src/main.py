"""Punto de entrada y bucle principal del menú de la CLI de EMT Madrid.

Interfaz interactiva íntegramente con stdlib y códigos de escape ANSI.
Permite seleccionar una línea, ver sus paradas, consultar tiempos de llegada
a una parada y listar las líneas que operan en una parada.
"""

import sys
from typing import Any, Dict, List, Optional

try:
    from .config import EMT_EMAIL, EMT_PASSWORD
    from .api_client import EMTClient, EMTApiError
    from . import ui
except ImportError:  # Ejecución directa como script (python src/main.py)
    from config import EMT_EMAIL, EMT_PASSWORD
    from api_client import EMTClient, EMTApiError
    import ui


# ---------------------------------------------------------------------------
# Parseo defensivo de las respuestas de la API
# ---------------------------------------------------------------------------

def _extraer_linea_info(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    """Extrae id, origen y destino de la respuesta de line_info."""
    if not data or "data" not in data or not data["data"]:
        return None
    item = data["data"][0]
    lid = (
        item.get("id")
        or item.get("lineId")
        or item.get("line")
        or item.get("codigo")
        or "-"
    )
    origen = (
        item.get("origin")
        or item.get("origen")
        or item.get("head")
        or item.get("destination")
        or item.get("destino")
        or "-"
    )
    destino = (
        item.get("destination")
        or item.get("destino")
        or item.get("tail")
        or item.get("origin")
        or item.get("origen")
        or "-"
    )
    return {"id": str(lid), "origen": str(origen), "destino": str(destino)}


def _extraer_paradas(data: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Extrae lista de paradas de la respuesta de line_stops."""
    paradas: List[Dict[str, str]] = []
    if not data or "data" not in data or not data["data"]:
        return paradas
    bloque = data["data"][0]
    lista = bloque.get("stops") or []
    for p in lista:
        paradas.append({
            "codigo": str(
                p.get("stop")
                or p.get("id")
                or p.get("codigo")
                or p.get("stopId")
                or "-"
            ),
            "nombre": str(p.get("name") or p.get("nombre") or "-"),
            "direccion": str(
                p.get("postalAddress")
                or p.get("address")
                or p.get("direccion")
                or "-"
            ),
        })
    return paradas


def _extraer_estimaciones(data: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Extrae estimaciones de llegada de la respuesta de stop_arrives.

    Estructura real: data[0].Arrive con campos line, destination,
    estimateArrive (en segundos).
    """
    estimaciones: List[Dict[str, str]] = []
    if not data or "data" not in data or not data["data"]:
        return estimaciones
    bloque = data["data"][0]
    lista = bloque.get("Arrive") or bloque.get("arrives") or bloque.get("estimations") or []
    # Si no hay clave conocida, intenta usar cualquier lista dentro del bloque
    if not lista and isinstance(bloque, dict):
        for valor in bloque.values():
            if isinstance(valor, list) and valor:
                lista = valor
                break
    for e in lista:
        if not isinstance(e, dict):
            continue
        estimate = e.get("estimateArrive") or e.get("estimate") or e.get("minutes") or e.get("min") or e.get("tiempo")
        if estimate is not None:
            try:
                minutos = str(int(int(estimate) / 60))
            except (ValueError, TypeError):
                minutos = str(estimate)
        else:
            minutos = "?"
        estimaciones.append({
            "linea": str(
                e.get("line") or e.get("linea") or e.get("id")
                or e.get("lineId") or "-"
            ),
            "destino": str(
                e.get("destination") or e.get("destino")
                or e.get("head") or e.get("nombre") or "-"
            ),
            "minutos": minutos,
        })
    return estimaciones


def _extraer_lineas_parada(data: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Extrae líneas que operan en una parada de la respuesta de stop_detail.

    Estructura real: data[0].stops[0].dataLine con campos line, label,
    direction, headerA (origen), headerB (destino).
    """
    lineas: List[Dict[str, str]] = []
    if not data or "data" not in data or not data["data"]:
        return lineas
    bloque = data["data"][0]
    # La respuesta real trae las líneas dentro de stops[0].dataLine
    lista: List[Any] = []
    stops = bloque.get("stops") or bloque.get("paradas") or []
    if isinstance(stops, list) and stops:
        primera = stops[0]
        if isinstance(primera, dict):
            lista = primera.get("dataLine") or primera.get("lineas") or []
    # Fallback: buscar cualquier lista en el bloque
    if not lista and isinstance(bloque, dict):
        for valor in bloque.values():
            if isinstance(valor, list) and valor:
                lista = valor
                break
    for l in lista:
        if not isinstance(l, dict):
            continue
        lineas.append({
            "id": str(
                l.get("line") or l.get("label") or l.get("id")
                or l.get("lineId") or l.get("codigo") or "-"
            ),
            "origen": str(
                l.get("headerA") or l.get("origin") or l.get("origen")
                or l.get("head") or l.get("nombre") or "-"
            ),
            "destino": str(
                l.get("headerB") or l.get("destination") or l.get("destino")
                or l.get("tail") or "-"
            ),
            "sentido": str(l.get("direction") or l.get("sentido") or "-"),
        })
    return lineas


def _extraer_paradas_listado(data: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Extrae código y nombre de paradas del listado de paradas (stops).

    La respuesta de stop_list() tiene 'data' como una lista directa de paradas,
    cada una con claves: node (código), name (nombre).
    """
    paradas: List[Dict[str, str]] = []
    if not data or "data" not in data or not isinstance(data["data"], list):
        return paradas
    for p in data["data"]:
        if not isinstance(p, dict):
            continue
        paradas.append({
            "codigo": str(
                p.get("node") or p.get("stop") or p.get("id")
                or p.get("codigo") or p.get("stopId") or "-"
            ),
            "nombre": str(p.get("name") or p.get("nombre") or "-"),
        })
    return paradas


def _buscar_paradas_por_nombre(
    client: EMTClient, nombre: str
) -> List[Dict[str, str]]:
    """Busca paradas cuyo nombre contiene el texto dado (case-insensitive).

    Consulta el listado de paradas de EMT y filtra localmente por nombre.
    Devuelve las coincidencias ordenadas tal como llegan de la API.
    """
    try:
        data = client.stop_list()
    except EMTApiError as exc:
        print(ui.error(f"No se pudo consultar el listado de paradas: {exc}"))
        return []
    paradas = _extraer_paradas_listado(data)
    texto = nombre.strip().lower()
    return [
        p for p in paradas if texto and texto in p["nombre"].lower() and p["nombre"] != "-"
    ]


def _mostrar_json_crudo(datos: Optional[Dict[str, Any]], etiqueta: str) -> None:
    """Muestra el JSON crudo recibido para depurar la estructura de la API."""
    import json as _json
    print(ui.error(f"No se pudo extraer información de {etiqueta}."))
    print(ui.info("Respuesta cruda de la API:"))
    print(_json.dumps(datos, indent=2, ensure_ascii=False)[:2000])


# ---------------------------------------------------------------------------
# Aplicación
# ---------------------------------------------------------------------------

class App:
    """Aplicación CLI: gestiona sesión, cliente API y bucle de menú."""

    def __init__(self) -> None:
        self.client: Optional[EMTClient] = None
        self.linea_activa: Optional[Dict[str, str]] = None
        self.paradas_activas: List[Dict[str, str]] = []
        self.autenticado = False

    def autenticar(self) -> bool:
        """Inicia sesión en la API y guarda el accessToken."""
        if not EMT_EMAIL or not EMT_PASSWORD:
            print(ui.error("Faltan credenciales: configura EMT_EMAIL y EMT_PASSWORD en .env"))
            return False
        self.client = EMTClient(email=EMT_EMAIL, password=EMT_PASSWORD)
        try:
            token = self.client.login()
        except EMTApiError as exc:
            print(ui.error(f"No se pudo autenticar: {exc}"))
            return False
        if not token:
            print(ui.error("Credenciales inválidas o token no obtenido."))
            return False
        self.autenticado = True
        print(ui.ok("Autenticación correcta."))
        ui.pausa("Pulsa Enter para abrir el menú...")
        return True

    def ejecutar(self) -> int:
        """Bucle principal de la aplicación."""
        if not EMT_EMAIL or not EMT_PASSWORD:
            print(ui.error("Faltan credenciales: copia .env.example a .env y rellénalo."))
            return 1
        if not self.autenticar():
            return 1

        while True:
            ui.limpiar_pantalla()
            ui.encabezado("Consulta de Autobuses EMT Madrid", self.linea_activa)
            ui.mostrar_menu()
            opcion = ui.prompt("Elige una opción:")

            if opcion == "1":
                self._opcion_seleccionar_linea()
            elif opcion == "2":
                self._opcion_mostrar_paradas()
            elif opcion == "3":
                self._opcion_tiempo_espera()
            elif opcion == "4":
                self._opcion_lineas_parada()
            elif opcion == "0":
                print(ui.info("¡Hasta luego!"))
                return 0
            else:
                print(ui.error("Opción no válida."))
                ui.pausa()

    # -- Opciones del menú ---------------------------------------------------

    def _requiere_linea(self) -> bool:
        """Devuelve True si hay línea activa; si no, pide seleccionar una."""
        if self.linea_activa:
            return True
        lid = ui.prompt("Primero selecciona una línea. Introduce su id (ej. 27, C1):")
        if lid:
            return self._seleccionar_linea_por_id(lid)
        return False

    def _seleccionar_linea_por_id(self, line_id: str) -> bool:
        assert self.client is not None
        # Intenta obtener info detallada (v1, con fallback v2 en api_client)
        try:
            data = self.client.line_info(line_id)
        except EMTApiError as exc:
            print(ui.error(f"No se pudo consultar la línea: {exc}"))
            ui.pausa()
            return False

        info = None
        if data is not None:
            info = _extraer_linea_info(data)

        # Si line_info falló (404), validar la línea mediante line_stops,
        # que sí responde para líneas como la 86 (como lo hace mostrar_paradas.py)
        if info is None or info["id"] == "-":
            try:
                paradas_data = self.client.line_stops(line_id, "1")
            except EMTApiError as exc:
                print(ui.error(f"No se pudo validar la línea '{line_id}': {exc}"))
                ui.pausa()
                return False
            paradas = _extraer_paradas(paradas_data)
            if not paradas:
                print(
                    ui.error(
                        f"No se encontró la línea '{line_id}'. "
                        f"Verifica el número e inténtalo de nuevo."
                    )
                )
                ui.pausa()
                return False
            info = {"id": line_id, "origen": "-", "destino": "-"}

        self.linea_activa = info
        self.paradas_activas = []  # resetear paradas al cambiar de línea
        print(
            ui.ok(
                f"Línea {info['id']} seleccionada ({info['origen']} → {info['destino']})."
            )
        )
        ui.pausa()
        return True

    def _opcion_seleccionar_linea(self) -> None:
        line_id = ui.prompt("Introduce el número o id de la línea (ej. 27, 146, C1, N12):")
        if line_id:
            self._seleccionar_linea_por_id(line_id)

    def _opcion_mostrar_paradas(self) -> None:
        if not self._requiere_linea():
            return
        assert self.client is not None and self.linea_activa is not None
        lid = self.linea_activa["id"]
        print(f"\nParadas de la línea {lid}\n")
        filas: List[List[str]] = []
        self.paradas_activas = []
        total = 0
        for direccion in ("1", "2"):
            try:
                data = self.client.line_stops(lid, direccion)
            except EMTApiError as exc:
                print(ui.error(f"Error consultando paradas (sentido {direccion}): {exc}"))
                continue
            paradas = _extraer_paradas(data)
            for p in paradas:
                self.paradas_activas.append(p)
                filas.append([str(len(self.paradas_activas)), p["codigo"], p["nombre"], p["direccion"], f"sentido {direccion}"])
            total += len(paradas)
        if not filas:
            print(ui.info("No se encontraron paradas."))
        else:
            ui.tabla(["#", "CÓDIGO", "NOMBRE", "DIRECCIÓN", "SENTIDO"], filas)
            print(f"\nTotal: {total} paradas")
        ui.pausa()

    def _seleccionar_parada(self) -> Optional[str]:
        """Permite elegir una parada por código o por nombre.

        No está limitado a la línea seleccionada: acepta un código numérico
        directo (ej. 70, 1890) o un nombre para buscar entre todas las paradas
        de EMT (ej. "Sol"). Devuelve el código de la parada o None si se cancela.
        """
        print("\nIntroduce el código de la parada (ej. 70, 1890) o un nombre "
              "para buscar (ej. Sol).")
        entrada = ui.prompt("Código o nombre de la parada (Enter para cancelar):")
        if not entrada:
            return None

        # Si es numérico, tratar como código directo
        if entrada.isdigit():
            return entrada

        # Buscar por nombre entre todas las paradas de EMT
        assert self.client is not None
        coincidencias = _buscar_paradas_por_nombre(self.client, entrada)
        if not coincidencias:
            print(ui.error(f"No se encontró ninguna parada con '{entrada}'."))
            ui.pausa()
            return None

        if len(coincidencias) == 1:
            p = coincidencias[0]
            print(ui.ok(f"Parada encontrada: {p['codigo']} — {p['nombre']}"))
            ui.pausa()
            return p["codigo"]

        # Varias coincidencias: pedir al usuario que elija
        print(f"\nSe encontraron {len(coincidencias)} paradas:")
        filas = [[str(i + 1), p["codigo"], p["nombre"]] for i, p in enumerate(coincidencias)]
        ui.tabla(["#", "CÓDIGO", "NOMBRE"], filas)
        opcion = ui.prompt(
            f"Elige una parada (1-{len(coincidencias)}) o Enter para cancelar:"
        )
        if not opcion:
            return None
        try:
            idx = int(opcion) - 1
            if 0 <= idx < len(coincidencias):
                return coincidencias[idx]["codigo"]
        except ValueError:
            pass
        print(ui.error("Opción no válida."))
        return None

    def _opcion_tiempo_espera(self) -> None:
        stop_id = self._seleccionar_parada()
        if not stop_id:
            return
        assert self.client is not None
        try:
            data = self.client.stop_arrives(stop_id)
        except EMTApiError as exc:
            print(ui.error(f"Error consultando tiempos de llegada: {exc}"))
            ui.pausa()
            return
        estimaciones = _extraer_estimaciones(data)
        if not estimaciones:
            _mostrar_json_crudo(data, "tiempos de llegada")
            ui.pausa()
            return
        print(f"\nTiempos de llegada a la parada {stop_id}\n")
        filas: List[List[str]] = []
        for e in estimaciones:
            try:
                minutos = int(e["minutos"])
            except ValueError:
                minutos = None
            filas.append([
                ui.formatear_minutos(minutos),
                ui.cian(e["linea"]),
                e["destino"],
            ])
        ui.tabla(["TIEMPO", "LÍNEA", "DESTINO"], filas)
        ui.pausa()

    def _opcion_lineas_parada(self) -> None:
        # No se limita a la línea seleccionada: acepta código o nombre de cualquier parada de EMT.
        stop_id = self._seleccionar_parada()
        if not stop_id:
            return
        assert self.client is not None
        try:
            data = self.client.stop_detail(stop_id)
        except EMTApiError as exc:
            print(ui.error(f"Error consultando detalle de parada: {exc}"))
            ui.pausa()
            return
        lineas = _extraer_lineas_parada(data)
        if not lineas:
            _mostrar_json_crudo(data, "detalle de parada")
            ui.pausa()
            return
        print(f"\nLíneas que llegan a la parada {stop_id}\n")
        filas = [[l["id"], l["origen"], l["destino"], l["sentido"]] for l in lineas]
        ui.tabla(["LÍNEA", "ORIGEN", "DESTINO", "SENTIDO"], filas)
        ui.pausa()


def main(argv: Optional[List[str]] = None) -> int:
    app = App()
    return app.ejecutar()


if __name__ == "__main__":
    sys.exit(main())
