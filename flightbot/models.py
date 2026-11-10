from dataclasses import dataclass


@dataclass(frozen=True)
class Flight:
    origin: str
    destination: str
    price: float
    currency: str
    departure_date: str  # YYYY-MM-DD
    airline: str = ""
    transfers: int = 0
    link: str = ""


@dataclass(frozen=True)
class Alert:
    id: int
    chat_id: int
    origin: str  # código IATA o país (AR / BR)
    destination: str
    max_price: float
    month: str | None = None  # YYYY-MM
    last_price: float | None = None  # último precio avisado
