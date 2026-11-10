"""Orígenes soportados: ciudades principales de Argentina y Brasil (códigos IATA)."""

import re

COUNTRY_ORIGINS: dict[str, list[str]] = {
    "AR": ["BUE", "COR", "MDZ", "ROS"],
    "BR": ["SAO", "RIO", "BSB", "CNF", "POA"],
}

_IATA = re.compile(r"^[A-Z]{3}$")


def is_iata(code: str) -> bool:
    return bool(_IATA.match(code))


def resolve_origins(text: str) -> list[str]:
    """Convierte 'AR', 'BR' o un código IATA en la lista de orígenes a consultar.

    Lanza ValueError si el texto no es ninguna de esas cosas.
    """
    code = text.strip().upper()
    if code in COUNTRY_ORIGINS:
        return list(COUNTRY_ORIGINS[code])
    if is_iata(code):
        return [code]
    raise ValueError(f"Origen inválido: {text!r}. Usá AR, BR o un código IATA (ej. BUE).")
