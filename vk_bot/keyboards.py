from __future__ import annotations

import json

OPEN_APP_LABEL = "Открыть Bloom Club"
REPEAT_CODE_LABEL = "Получить код повторно"
REPEAT_CODE_PAYLOAD = {"command": "get_code"}


def login_keyboard(app_url: str) -> str:
    keyboard = {
        "inline": True,
        "buttons": [
            [{"action": {"type": "open_link", "link": app_url, "label": OPEN_APP_LABEL}}],
            [{"action": {"type": "text", "label": REPEAT_CODE_LABEL, "payload": json.dumps(REPEAT_CODE_PAYLOAD, ensure_ascii=False)}, "color": "primary"}],
        ],
    }
    return json.dumps(keyboard, ensure_ascii=False)
