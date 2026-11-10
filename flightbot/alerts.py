"""Revisión periódica de alertas de precio."""

from flightbot.airports import resolve_origins
from flightbot.models import Alert, Flight
from flightbot.providers import FlightProvider, ProviderError
from flightbot.search import format_flight, search_cheapest
from flightbot.storage import Storage


def should_notify(alert: Alert, flight: Flight) -> bool:
    """Avisa si el precio está bajo el tope y es menor al último que ya se avisó."""
    if flight.price > alert.max_price:
        return False
    return alert.last_price is None or flight.price < alert.last_price


def check_alerts(provider: FlightProvider, storage: Storage) -> list[tuple[int, str]]:
    """Devuelve los mensajes a enviar como pares (chat_id, texto)."""
    messages: list[tuple[int, str]] = []
    for alert in storage.alerts():
        try:
            found = search_cheapest(
                provider, resolve_origins(alert.origin), alert.destination, alert.month, limit=1
            )
        except ProviderError:
            continue  # se reintenta en la próxima revisión
        if not found or not should_notify(alert, found[0]):
            continue
        storage.set_last_price(alert.id, found[0].price)
        messages.append(
            (alert.chat_id, f"🔔 Alerta #{alert.id}: bajó de tu tope\n{format_flight(found[0])}")
        )
    return messages
