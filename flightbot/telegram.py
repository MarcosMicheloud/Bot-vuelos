"""Cliente mínimo de la Bot API de Telegram (long polling)."""

from flightbot.httpjson import HttpError, get_json, post_json

API = "https://api.telegram.org/bot{token}/{method}"


class TelegramClient:
    def __init__(self, token: str):
        self.token = token
        self.offset = 0

    def updates(self, timeout: int = 25) -> list[tuple[int, str]]:
        """Mensajes de texto nuevos como pares (chat_id, texto)."""
        body = get_json(
            API.format(token=self.token, method="getUpdates"),
            params={"offset": self.offset, "timeout": timeout},
            timeout=timeout + 10,
        )
        if not body.get("ok"):
            raise HttpError(f"Telegram: {body.get('description', 'error')}")
        messages = []
        for update in body["result"]:
            self.offset = update["update_id"] + 1
            message = update.get("message") or {}
            if "text" in message:
                messages.append((message["chat"]["id"], message["text"]))
        return messages

    def send(self, chat_id: int, text: str) -> None:
        post_json(
            API.format(token=self.token, method="sendMessage"),
            {"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
        )
