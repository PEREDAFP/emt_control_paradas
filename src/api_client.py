"""Cliente HTTP para la API de EMT Madrid usando solo urllib (stdlib).

No usa requests ni httpx. Gestiona el accessToken de autenticación y expone
los endpoints necesarios para la CLI de autobuses.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

try:
    from .config import EMT_EMAIL, EMT_PASSWORD
except ImportError:  # Ejecución directa como script (python src/api_client.py)
    from config import EMT_EMAIL, EMT_PASSWORD

BASE_URL = "https://openapi.emtmadrid.es/"


class EMTApiError(Exception):
    """Error levantado por el cliente de la API de EMT."""


class EMTClient:
    """Cliente de la API MobilityLabs / OpenAPI EMT Madrid."""

    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        base_url: str = BASE_URL,
    ):
        self.email = email or EMT_EMAIL
        self.password = password or EMT_PASSWORD
        self.base_url = base_url.rstrip("/")
        self.access_token: Optional[str] = None

    def _request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        params: Optional[Dict[str, str]] = None,
        auth: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Efectúa una petición HTTP y devuelve el JSON decodificado."""
        url = self.base_url + path
        if params:
            url += "?" + urllib.parse.urlencode(params)

        req_headers: Dict[str, str] = {"Accept": "application/json"}
        if auth and self.access_token:
            req_headers["accessToken"] = self.access_token
        if headers:
            req_headers.update(headers)

        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            req_headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            url, data=body, headers=req_headers, method=method
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                if not raw:
                    return None
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise EMTApiError(f"HTTP {exc.code} al llamar {path}") from exc
        except urllib.error.URLError as exc:
            raise EMTApiError(
                f"Error de red al llamar {path}: {exc.reason}"
            ) from exc

    def login(self) -> Optional[str]:
        """Autentica contra la API y guarda el accessToken.

        Endpoint: GET /v1/mobilitylabs/user/login/
        Cabeceras: email, password.
        Respuesta: data[0]["accessToken"].
        """
        headers = {"email": self.email, "password": self.password}
        data = self._request(
            "GET", "/v1/mobilitylabs/user/login/", headers=headers, auth=False
        )
        token = None
        if data and "data" in data and len(data["data"]) > 0:
            token = data["data"][0].get("accessToken")
        self.access_token = token
        return token

    def line_info(self, line_id: str) -> Optional[Dict[str, Any]]:
        """Información de una línea de autobús.

        Endpoint: GET /v1/transport/busemtmad/lines/{lineId}/info/
        """
        return self._request(
            "GET", f"/v1/transport/busemtmad/lines/{line_id}/info/"
        )

    def line_stops(
        self, line_id: str, direction: str
    ) -> Optional[Dict[str, Any]]:
        """Paradas de una línea en un sentido.

        Endpoint: GET /v1/transport/busemtmad/lines/{lineId}/stops/{direction}/
        """
        return self._request(
            "GET", f"/v1/transport/busemtmad/lines/{line_id}/stops/{direction}/"
        )

    def stop_arrives(
        self, stop_id: str, culture_info: str = "ES"
    ) -> Optional[Dict[str, Any]]:
        """Tiempos estimados de llegada a una parada.

        Endpoint: POST /v2/transport/busemtmad/stops/{stopId}/arrives/
        """
        payload = {
            "cultureInfo": culture_info,
            "Text_StopRequired_YN": "Y",
            "Text_EstimationsRequired_YN": "Y",
            "Text_IncidencesRequired_YN": "N",
        }
        return self._request(
            "POST",
            f"/v2/transport/busemtmad/stops/{stop_id}/arrives/",
            data=payload,
        )

    def stop_detail(self, stop_id: str) -> Optional[Dict[str, Any]]:
        """Detalle de una parada y las líneas que operan en ella.

        Endpoint: GET /v1/transport/busemtmad/stops/{stopId}/detail/
        """
        return self._request(
            "GET", f"/v1/transport/busemtmad/stops/{stop_id}/detail/"
        )
