"""Comandos del bot: reciben texto y devuelven texto, sin depender de Telegram."""

import re

from flightbot.airports import is_iata, resolve_origins
from flightbot.providers import FlightProvider, ProviderError
from flightbot.search import format_flight, search_cheapest
from flightbot.storage import Storage

HELP = """✈️ Busco vuelos baratos desde Argentina o Brasil.

/buscar ORIGEN DESTINO [MES] — los más baratos en una ruta
/ofertas ORIGEN [MES] — los más baratos a cualquier destino
/alerta ORIGEN DESTINO PRECIO [MES] — te aviso cuando baje de ese precio (USD)
/alertas — tus alertas
/borrar ID — borra una alerta

ORIGEN: AR, BR o un código IATA (BUE, COR, SAO, RIO...).
MES: AAAA-MM, por ejemplo 2026-12.
Ejemplo: /buscar AR MIA 2026-12"""

_MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class UsageError(Exception):
    """El usuario escribió mal un comando; el mensaje se le muestra tal cual."""


class CommandHandler:
    def __init__(self, provider: FlightProvider, storage: Storage):
        self.provider = provider
        self.storage = storage

    def handle(self, chat_id: int, text: str) -> str:
        parts = text.split()
        if not parts or not parts[0].startswith("/"):
            return HELP
        name = parts[0][1:].split("@")[0].lower()
        command = {
            "buscar": self._buscar,
            "ofertas": self._ofertas,
            "alerta": self._alerta,
            "alertas": self._alertas,
            "borrar": self._borrar,
        }.get(name)
        if command is None:
            return HELP
        try:
            return command(chat_id, parts[1:])
        except UsageError as error:
            return f"⚠️ {error}"
        except ProviderError:
            return "⚠️ No pude consultar los precios ahora. Probá de nuevo en unos minutos."

    def _buscar(self, chat_id: int, args: list[str]) -> str:
        if len(args) not in (2, 3):
            raise UsageError("Uso: /buscar ORIGEN DESTINO [MES]")
        origins = _origins(args[0])
        destination = _destination(args[1])
        month = _month(args[2]) if len(args) == 3 else None
        flights = search_cheapest(self.provider, origins, destination, month)
        return _listing(flights)

    def _ofertas(self, chat_id: int, args: list[str]) -> str:
        if len(args) not in (1, 2):
            raise UsageError("Uso: /ofertas ORIGEN [MES]")
        origins = _origins(args[0])
        month = _month(args[1]) if len(args) == 2 else None
        return _listing(search_cheapest(self.provider, origins, None, month))

    def _alerta(self, chat_id: int, args: list[str]) -> str:
        if len(args) not in (3, 4):
            raise UsageError("Uso: /alerta ORIGEN DESTINO PRECIO [MES]")
        _origins(args[0])  # solo valida
        origin = args[0].upper()
        destination = _destination(args[1])
        try:
            max_price = float(args[2].replace(",", "."))
        except ValueError:
            raise UsageError(f"Precio inválido: {args[2]}") from None
        if max_price <= 0:
            raise UsageError("El precio tiene que ser mayor a cero.")
        month = _month(args[3]) if len(args) == 4 else None
        alert = self.storage.add_alert(chat_id, origin, destination, max_price, month)
        return (
            f"✅ Alerta #{alert.id}: {origin} → {destination} "
            f"por USD {max_price:.0f} o menos{_when(month)}."
        )

    def _alertas(self, chat_id: int, args: list[str]) -> str:
        alerts = self.storage.alerts(chat_id)
        if not alerts:
            return "No tenés alertas. Creá una con /alerta ORIGEN DESTINO PRECIO [MES]."
        return "\n".join(
            f"#{a.id}  {a.origin} → {a.destination}  ≤ USD {a.max_price:.0f}{_when(a.month)}"
            for a in alerts
        )

    def _borrar(self, chat_id: int, args: list[str]) -> str:
        if len(args) != 1 or not args[0].lstrip("#").isdigit():
            raise UsageError("Uso: /borrar ID")
        alert_id = int(args[0].lstrip("#"))
        if self.storage.delete_alert(chat_id, alert_id):
            return f"🗑️ Alerta #{alert_id} borrada."
        return f"No encontré la alerta #{alert_id}."


def _origins(text: str) -> list[str]:
    try:
        return resolve_origins(text)
    except ValueError as error:
        raise UsageError(str(error)) from None


def _destination(text: str) -> str:
    code = text.upper()
    if not is_iata(code):
        raise UsageError(f"Destino inválido: {text}. Usá un código IATA (ej. MIA).")
    return code


def _month(text: str) -> str:
    if not _MONTH.match(text):
        raise UsageError(f"Mes inválido: {text}. Usá AAAA-MM (ej. 2026-12).")
    return text


def _when(month: str | None) -> str:
    return f" en {month}" if month else ""


def _listing(flights) -> str:
    if not flights:
        return "No encontré vuelos para esa búsqueda."
    return "\n\n".join(format_flight(f) for f in flights)
