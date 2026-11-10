"""Búsqueda del vuelo más barato combinando varios orígenes."""

from flightbot.models import Flight
from flightbot.providers import FlightProvider, ProviderError


def search_cheapest(
    provider: FlightProvider,
    origins: list[str],
    destination: str | None = None,
    month: str | None = None,
    limit: int = 5,
) -> list[Flight]:
    """Los `limit` vuelos más baratos entre todos los orígenes.

    Si un origen falla se sigue con los demás; si fallan todos, se propaga el error.
    """
    flights: list[Flight] = []
    last_error: ProviderError | None = None
    failures = 0
    for origin in origins:
        try:
            flights.extend(provider.cheapest(origin, destination, month))
        except ProviderError as error:
            last_error = error
            failures += 1
    if last_error is not None and failures == len(origins):
        raise last_error
    return sorted(flights, key=lambda f: f.price)[:limit]


def format_flight(flight: Flight) -> str:
    stops = "directo" if flight.transfers == 0 else f"{flight.transfers} escala(s)"
    line = (
        f"{flight.origin} → {flight.destination}  {flight.currency} {flight.price:.0f}"
        f"  {flight.departure_date}  {flight.airline} {stops}".rstrip()
    )
    return f"{line}\n{flight.link}" if flight.link else line
