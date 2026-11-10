import pytest

from flightbot.airports import resolve_origins
from flightbot.alerts import check_alerts, should_notify
from flightbot.commands import HELP, CommandHandler
from flightbot.httpjson import HttpError
from flightbot.models import Alert, Flight
from flightbot.providers import ProviderError
from flightbot.providers.demo import DemoProvider
from flightbot.providers.travelpayouts import TravelpayoutsProvider
from flightbot.search import format_flight, search_cheapest
from flightbot.storage import Storage


class BrokenProvider:
    def __init__(self, broken_origins=None):
        self.broken = broken_origins

    def cheapest(self, origin, destination=None, month=None):
        if self.broken is None or origin in self.broken:
            raise ProviderError("caído")
        return DemoProvider().cheapest(origin, destination, month)


@pytest.fixture
def storage():
    return Storage()


@pytest.fixture
def handler(storage):
    return CommandHandler(DemoProvider(), storage)


# --- orígenes ---

def test_resolve_country_and_iata():
    assert resolve_origins("ar") == ["BUE", "COR", "MDZ", "ROS"]
    assert "SAO" in resolve_origins("BR")
    assert resolve_origins("eze") == ["EZE"]


def test_resolve_invalid_origin():
    with pytest.raises(ValueError):
        resolve_origins("Buenos Aires")


# --- búsqueda ---

def test_search_merges_origins_sorted_by_price():
    flights = search_cheapest(DemoProvider(), ["BUE", "COR"], "MIA")
    assert [(f.origin, f.price) for f in flights] == [("BUE", 412), ("COR", 530)]


def test_search_filters_month_and_limits():
    assert search_cheapest(DemoProvider(), ["SAO"], None, "2027-01")[0].destination == "LIS"
    assert len(search_cheapest(DemoProvider(), ["BUE"], limit=2)) == 2


def test_search_survives_one_broken_origin():
    flights = search_cheapest(BrokenProvider({"COR"}), ["BUE", "COR"], "MIA")
    assert [f.origin for f in flights] == ["BUE"]


def test_search_raises_when_every_origin_fails():
    with pytest.raises(ProviderError):
        search_cheapest(BrokenProvider(), ["BUE", "COR"], "MIA")


def test_format_flight():
    text = format_flight(Flight("BUE", "MIA", 412.4, "USD", "2026-12-03", "AR", 1, "https://x"))
    assert text == "BUE → MIA  USD 412  2026-12-03  AR 1 escala(s)\nhttps://x"


# --- Travelpayouts ---

def test_travelpayouts_parses_response_and_sends_params():
    calls = {}

    def fetch(url, params, headers):
        calls.update(params=params, headers=headers)
        return {
            "success": True,
            "currency": "usd",
            "data": [
                {
                    "origin": "BUE",
                    "destination": "MIA",
                    "price": 410,
                    "airline": "AR",
                    "departure_at": "2026-12-03T08:15:00-03:00",
                    "transfers": 0,
                    "link": "/search/BUE0312MIA1",
                }
            ],
        }

    flights = TravelpayoutsProvider("tok", fetch=fetch).cheapest("BUE", "MIA", "2026-12")
    assert flights == [
        Flight("BUE", "MIA", 410.0, "USD", "2026-12-03", "AR", 0,
               "https://www.aviasales.com/search/BUE0312MIA1")
    ]
    assert calls["params"]["destination"] == "MIA"
    assert calls["params"]["departure_at"] == "2026-12"
    assert calls["headers"] == {"X-Access-Token": "tok"}


def test_travelpayouts_omits_optional_params():
    seen = {}

    def fetch(url, params, headers):
        seen.update(params)
        return {"success": True, "data": []}

    assert TravelpayoutsProvider("tok", fetch=fetch).cheapest("SAO") == []
    assert "destination" not in seen and "departure_at" not in seen


def test_travelpayouts_errors_become_provider_errors():
    def http_fails(url, params, headers):
        raise HttpError("HTTP 500")

    with pytest.raises(ProviderError):
        TravelpayoutsProvider("tok", fetch=http_fails).cheapest("BUE")
    with pytest.raises(ProviderError):
        TravelpayoutsProvider("tok", fetch=lambda *a, **k: {"success": False}).cheapest("BUE")


# --- almacenamiento ---

def test_storage_alerts_are_per_chat(storage):
    first = storage.add_alert(1, "AR", "MIA", 400, None)
    storage.add_alert(2, "BR", "LIS", 500, "2027-01")
    assert storage.alerts(1) == [Alert(first.id, 1, "AR", "MIA", 400, None, None)]
    assert len(storage.alerts()) == 2
    assert storage.delete_alert(2, first.id) is False  # no es su alerta
    assert storage.delete_alert(1, first.id) is True
    assert storage.alerts(1) == []


# --- alertas ---

def test_should_notify_rules():
    flight = Flight("BUE", "MIA", 400, "USD", "2026-12-03")
    assert should_notify(Alert(1, 1, "BUE", "MIA", 400), flight)
    assert not should_notify(Alert(1, 1, "BUE", "MIA", 399), flight)
    assert not should_notify(Alert(1, 1, "BUE", "MIA", 500, None, 400), flight)
    assert should_notify(Alert(1, 1, "BUE", "MIA", 500, None, 401), flight)


def test_check_alerts_notifies_once_until_price_drops(storage):
    storage.add_alert(7, "AR", "MIA", 450, None)
    storage.add_alert(7, "AR", "MAD", 300, None)  # nunca se cumple
    provider = DemoProvider()

    messages = check_alerts(provider, storage)
    assert len(messages) == 1
    assert messages[0][0] == 7 and "USD 412" in messages[0][1]
    assert check_alerts(provider, storage) == []  # mismo precio: no repite

    provider.flights.append(Flight("ROS", "MIA", 380, "USD", "2026-12-09"))
    assert "USD 380" in check_alerts(provider, storage)[0][1]


def test_check_alerts_skips_when_provider_is_down(storage):
    storage.add_alert(7, "AR", "MIA", 450, None)
    assert check_alerts(BrokenProvider(), storage) == []
    assert storage.alerts()[0].last_price is None


# --- comandos ---

def test_help_for_unknown_text(handler):
    assert handler.handle(1, "hola") == HELP
    assert handler.handle(1, "/start") == HELP
    assert handler.handle(1, "") == HELP


def test_buscar(handler):
    reply = handler.handle(1, "/buscar ar mia")
    assert reply.splitlines()[0].startswith("BUE → MIA  USD 412")
    assert "COR → MIA" in reply


def test_buscar_with_bot_mention_and_month(handler):
    assert "SAO → LIS" in handler.handle(1, "/buscar@VuelosBot SAO LIS 2027-01")
    assert handler.handle(1, "/buscar SAO LIS 2026-12") == "No encontré vuelos para esa búsqueda."


def test_ofertas(handler):
    assert handler.handle(1, "/ofertas BR").startswith("RIO → BUE  USD 120")


@pytest.mark.parametrize(
    "text, expected",
    [
        ("/buscar BUE", "Uso: /buscar"),
        ("/buscar Argentina MIA", "Origen inválido"),
        ("/buscar BUE Miami", "Destino inválido"),
        ("/buscar BUE MIA 2026-13", "Mes inválido"),
        ("/alerta BUE MIA barato", "Precio inválido"),
        ("/alerta BUE MIA -5", "mayor a cero"),
        ("/borrar todo", "Uso: /borrar"),
    ],
)
def test_usage_errors(handler, text, expected):
    assert expected in handler.handle(1, text)


def test_alert_lifecycle(handler):
    assert handler.handle(1, "/alertas").startswith("No tenés alertas")
    assert "Alerta #1: AR → MIA por USD 400 o menos en 2026-12" in handler.handle(
        1, "/alerta ar mia 400 2026-12"
    )
    assert handler.handle(1, "/alertas") == "#1  AR → MIA  ≤ USD 400 en 2026-12"
    assert handler.handle(2, "/borrar 1") == "No encontré la alerta #1."
    assert handler.handle(1, "/borrar #1") == "🗑️ Alerta #1 borrada."


def test_provider_failure_is_reported(storage):
    reply = CommandHandler(BrokenProvider(), storage).handle(1, "/buscar BUE MIA")
    assert "No pude consultar los precios" in reply
