from __future__ import annotations

import json

OPEN_APP_LABEL = "Открыть приложение"


def login_keyboard(app_url: str) -> str:
    keyboard = {
        "inline": False,
        "one_time": False,
        "buttons": [
            [{"action": {"type": "open_link", "link": app_url, "label": OPEN_APP_LABEL}}],
        ],
    }
    return json.dumps(keyboard, ensure_ascii=False)
