from typing import Protocol

from flightbot.models import Flight


class ProviderError(Exception):
    """La fuente de precios falló o devolvió algo inesperado."""


class FlightProvider(Protocol):
    def cheapest(
        self, origin: str, destination: str | None = None, month: str | None = None
    ) -> list[Flight]:
        """Vuelos más baratos desde `origin`. Sin destino: a cualquier lugar."""
        ...
