"""Alertas de precio guardadas en SQLite."""

import sqlite3

from flightbot.models import Alert

_SCHEMA = """
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    max_price REAL NOT NULL,
    month TEXT,
    last_price REAL
)
"""
_COLUMNS = "id, chat_id, origin, destination, max_price, month, last_price"


class Storage:
    def __init__(self, path: str = ":memory:"):
        self.db = sqlite3.connect(path)
        self.db.execute(_SCHEMA)
        self.db.commit()

    def add_alert(
        self, chat_id: int, origin: str, destination: str, max_price: float, month: str | None
    ) -> Alert:
        cursor = self.db.execute(
            "INSERT INTO alerts (chat_id, origin, destination, max_price, month) VALUES (?, ?, ?, ?, ?)",
            (chat_id, origin, destination, max_price, month),
        )
        self.db.commit()
        return Alert(cursor.lastrowid, chat_id, origin, destination, max_price, month)

    def alerts(self, chat_id: int | None = None) -> list[Alert]:
        query = f"SELECT {_COLUMNS} FROM alerts"
        args: tuple = ()
        if chat_id is not None:
            query += " WHERE chat_id = ?"
            args = (chat_id,)
        return [Alert(*row) for row in self.db.execute(query + " ORDER BY id", args)]

    def delete_alert(self, chat_id: int, alert_id: int) -> bool:
        cursor = self.db.execute(
            "DELETE FROM alerts WHERE id = ? AND chat_id = ?", (alert_id, chat_id)
        )
        self.db.commit()
        return cursor.rowcount > 0

    def set_last_price(self, alert_id: int, price: float) -> None:
        self.db.execute("UPDATE alerts SET last_price = ? WHERE id = ?", (price, alert_id))
        self.db.commit()
