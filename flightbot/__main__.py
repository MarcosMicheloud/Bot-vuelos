"""Punto de entrada.

    py -m flightbot run            # bot de Telegram
    py -m flightbot cli "/buscar AR MIA"   # prueba un comando sin Telegram
Agregá --demo para usar precios inventados en vez de Travelpayouts.
"""

import argparse
import os
import sys
import time

from flightbot.alerts import check_alerts
from flightbot.commands import CommandHandler
from flightbot.httpjson import HttpError
from flightbot.providers.demo import DemoProvider
from flightbot.providers.travelpayouts import TravelpayoutsProvider
from flightbot.storage import Storage
from flightbot.telegram import TelegramClient


def load_env(path: str = ".env") -> None:
    """Carga pares CLAVE=valor de un archivo .env sin pisar variables ya definidas."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def require(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        sys.exit(f"Falta {name}. Copiá .env.example a .env y completalo (o usá --demo).")
    return value


def build_provider(demo: bool):
    return DemoProvider() if demo else TravelpayoutsProvider(require("TRAVELPAYOUTS_TOKEN"))


def run(handler: CommandHandler, provider, storage: Storage) -> None:
    telegram = TelegramClient(require("TELEGRAM_TOKEN"))
    interval = int(os.environ.get("ALERT_INTERVAL_MINUTES", "60")) * 60
    next_check = time.monotonic()
    print("Bot en marcha. Ctrl+C para detenerlo.")
    while True:
        try:
            for chat_id, text in telegram.updates():
                telegram.send(chat_id, handler.handle(chat_id, text))
            if time.monotonic() >= next_check:
                next_check = time.monotonic() + interval
                for chat_id, text in check_alerts(provider, storage):
                    telegram.send(chat_id, text)
        except HttpError as error:
            print(f"Error de red: {error}. Reintento en 5 s.", file=sys.stderr)
            time.sleep(5)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="flightbot", description="Bot de vuelos baratos")
    parser.add_argument("--demo", action="store_true", help="usa precios inventados")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("run", help="inicia el bot de Telegram")
    cli = sub.add_parser("cli", help="ejecuta un comando y muestra la respuesta")
    cli.add_argument("text")
    args = parser.parse_args()

    load_env()
    provider = build_provider(args.demo)
    storage = Storage(os.environ.get("DATABASE_PATH", "flightbot.db"))
    handler = CommandHandler(provider, storage)
    if args.mode == "cli":
        print(handler.handle(0, args.text))
    else:
        try:
            run(handler, provider, storage)
        except KeyboardInterrupt:
            print("\nBot detenido.")


if __name__ == "__main__":
    main()
