from __future__ import annotations

import json

OPEN_APP_LABEL = "Открыть Bloom Club"
REPEAT_CODE_LABEL = "Получить код повторно"
NEW_CODE_LABEL = "Получить новый код"
REPEAT_CODE_PAYLOAD = {"command": "get_code"}


def login_keyboard(app_url: str, *, repeat_label: str = REPEAT_CODE_LABEL) -> str:
    keyboard = {
        "inline": True,
        "buttons": [
            [{"action": {"type": "open_link", "link": app_url, "label": OPEN_APP_LABEL}}],
            [{"action": {"type": "text", "label": repeat_label, "payload": json.dumps(REPEAT_CODE_PAYLOAD, ensure_ascii=False)}, "color": "primary"}],
        ],
    }
    return json.dumps(keyboard, ensure_ascii=False)


def partner_confirmation_keyboard(session_id: int) -> str:
    keyboard = {
        "inline": True,
        "buttons": [[
            {"action": {"type": "text", "label": "Да, активировать", "payload": json.dumps({"command": "confirm_partner_code", "session_id": session_id}, ensure_ascii=False)}, "color": "positive"},
            {"action": {"type": "text", "label": "Нет", "payload": json.dumps({"command": "cancel_partner_code"}, ensure_ascii=False)}, "color": "secondary"},
        ]],
    }
    return json.dumps(keyboard, ensure_ascii=False)
