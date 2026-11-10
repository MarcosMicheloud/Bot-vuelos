# flightbot

Bot de Telegram que busca vuelos baratos desde Argentina o Brasil y avisa cuando una ruta baja de un precio tope.

Los precios salen de la [Aviasales Data API](https://support.travelpayouts.com/hc/en-us/articles/203956163) de Travelpayouts. Son precios en caché (lo que encontraron otros usuarios en las últimas 48 horas), no una búsqueda en vivo: sirven para detectar ofertas, y el precio final se confirma en el enlace.

## Comandos

| Comando | Qué hace |
| --- | --- |
| `/buscar ORIGEN DESTINO [MES]` | Los vuelos más baratos en una ruta |
| `/ofertas ORIGEN [MES]` | Los más baratos a cualquier destino |
| `/alerta ORIGEN DESTINO PRECIO [MES]` | Avisa cuando la ruta baja de ese precio (USD) |
| `/alertas` | Lista tus alertas |
| `/borrar ID` | Borra una alerta |

`ORIGEN` es `AR`, `BR` o un código IATA (`BUE`, `COR`, `SAO`, `RIO`...). Con `AR` o `BR` se consultan las ciudades principales del país. `MES` va como `AAAA-MM`.

## Probarlo sin tokens

Requiere Python 3.10 o superior y ninguna dependencia externa.

```bash
py -m flightbot --demo cli "/buscar AR MIA"
```

`--demo` usa precios inventados y `cli` ejecuta un comando sin pasar por Telegram.

## Correr el bot

1. Creá un bot con [@BotFather](https://t.me/BotFather) y copiá su token.
2. Registrate en [Travelpayouts](https://www.travelpayouts.com), sumate al programa de Aviasales y copiá el token de la API desde tu perfil.
3. Copiá `.env.example` a `.env` y completá los dos tokens.

```bash
py -m flightbot run
```

## Tests

```bash
py -m pip install -r requirements-dev.txt
```

```bash
py -m pytest
```

## Estructura

```
flightbot/
  commands.py      comandos: texto de entrada, texto de salida
  search.py        combina orígenes y ordena por precio
  alerts.py        decide cuándo avisar
  storage.py       alertas en SQLite
  airports.py      orígenes de Argentina y Brasil
  providers/       fuentes de precios (Travelpayouts, demo)
  telegram.py      cliente de la Bot API (long polling)
  __main__.py      arranque y configuración
tests/
```

Para sumar otra fuente de precios alcanza con una clase que tenga el método `cheapest(origin, destination, month)`.

## Pendientes

- Vuelos ida y vuelta, con duración de estadía.
- Historial de precios por ruta y comando `/historial`.
- Precios en ARS y BRL además de USD.
- Nombres de ciudades además de códigos IATA (`/buscar "Buenos Aires" Miami`).
- Resumen diario con las mejores ofertas.
- Filtro de solo vuelos directos.
