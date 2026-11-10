"""GET/POST que devuelven JSON, con la librería estándar."""

import json
import urllib.error
import urllib.parse
import urllib.request


class HttpError(Exception):
    pass


def get_json(url: str, params: dict | None = None, headers: dict | None = None, timeout: float = 30):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    return _send(urllib.request.Request(url, headers=headers or {}), timeout)


def post_json(url: str, payload: dict, timeout: float = 30):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    return _send(request, timeout)


def _send(request: urllib.request.Request, timeout: float):
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise HttpError(f"HTTP {error.code}") from error
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise HttpError(str(error)) from error
