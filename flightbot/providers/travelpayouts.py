"""Precios de la Aviasales Data API (Travelpayouts).

Devuelve los pasajes más baratos que encontraron usuarios de Aviasales en las
últimas 48 horas: son precios en caché, no una búsqueda en vivo.
Docs: https://support.travelpayouts.com/hc/en-us/articles/203956163
"""

from typing import Callable

from flightbot.httpjson import HttpError, get_json
from flightbot.models import Flight
from flightbot.providers import ProviderError

API_URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
LINK_BASE = "https://www.aviasales.com"


class TravelpayoutsProvider:
    def __init__(self, token: str, currency: str = "usd", fetch: Callable = get_json):
        self.token = token
        self.currency = currency
        self.fetch = fetch

    def cheapest(
        self, origin: str, destination: str | None = None, month: str | None = None
    ) -> list[Flight]:
        params = {
            "origin": origin,
            "currency": self.currency,
            "sorting": "price",
            "one_way": "true",
            "limit": 30,
        }
        if destination:
            params["destination"] = destination
        if month:
            params["departure_at"] = month
        try:
            body = self.fetch(API_URL, params=params, headers={"X-Access-Token": self.token})
        except HttpError as error:
            raise ProviderError(f"Travelpayouts no respondió: {error}") from error
        if not isinstance(body, dict) or not body.get("success"):
            raise ProviderError(f"Travelpayouts devolvió un error: {body!r}")
        currency = str(body.get("currency", self.currency)).upper()
        return [self._to_flight(item, currency) for item in body.get("data", [])]

    @staticmethod
    def _to_flight(item: dict, currency: str) -> Flight:
        link = item.get("link", "")
        return Flight(
            origin=item["origin"],
            destination=item["destination"],
            price=float(item["price"]),
            currency=currency,
            departure_date=str(item.get("departure_at", ""))[:10],
            airline=item.get("airline", ""),
            transfers=int(item.get("transfers", 0)),
            link=f"{LINK_BASE}{link}" if link else "",
        )
