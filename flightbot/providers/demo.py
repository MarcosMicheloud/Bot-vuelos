"""Proveedor con datos inventados, para probar el bot sin token y para los tests."""

from flightbot.models import Flight

SAMPLE = [
    Flight("BUE", "MIA", 412, "USD", "2026-12-03", "AR", 0),
    Flight("BUE", "MAD", 689, "USD", "2026-12-10", "IB", 0),
    Flight("BUE", "SCL", 98, "USD", "2026-12-05", "JA", 0),
    Flight("COR", "MIA", 530, "USD", "2026-12-08", "CM", 1),
    Flight("SAO", "MIA", 355, "USD", "2026-12-04", "LA", 0),
    Flight("SAO", "LIS", 498, "USD", "2027-01-12", "TP", 0),
    Flight("RIO", "MAD", 540, "USD", "2027-01-15", "UX", 1),
    Flight("RIO", "BUE", 120, "USD", "2026-12-20", "G3", 0),
]


class DemoProvider:
    def __init__(self, flights: list[Flight] | None = None):
        self.flights = list(SAMPLE if flights is None else flights)

    def cheapest(
        self, origin: str, destination: str | None = None, month: str | None = None
    ) -> list[Flight]:
        found = [
            f
            for f in self.flights
            if f.origin == origin
            and (destination is None or f.destination == destination)
            and (month is None or f.departure_date.startswith(month))
        ]
        return sorted(found, key=lambda f: f.price)
