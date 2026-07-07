from __future__ import annotations

from urllib.parse import parse_qsl


def parse_options_header(value: str | bytes | None) -> tuple[bytes, dict[bytes, bytes]]:
    if value is None:
        return b"", {}
    raw = value if isinstance(value, bytes) else value.encode("latin-1")
    parts = [part.strip() for part in raw.split(b";")]
    disposition = parts[0].lower() if parts else b""
    options: dict[bytes, bytes] = {}
    for part in parts[1:]:
        if b"=" not in part:
            continue
        key, option_value = part.split(b"=", 1)
        option_value = option_value.strip()
        if len(option_value) >= 2 and option_value[:1] == option_value[-1:] == b'"':
            option_value = option_value[1:-1]
        options[key.strip().lower()] = option_value
    return disposition, options


class MultipartParser:
    def __init__(self, boundary: str | bytes, callbacks: dict[str, object]) -> None:
        self.boundary = boundary if isinstance(boundary, bytes) else boundary.encode("latin-1")
        self.callbacks = callbacks
        self._buffer = bytearray()

    def write(self, data: bytes) -> None:
        self._buffer.extend(data)
        final_delimiter = b"--" + self.boundary + b"--"
        if final_delimiter in self._buffer:
            self._parse_buffer()

    def finalize(self) -> None:
        if self._buffer:
            self._parse_buffer()

    def _parse_buffer(self) -> None:
        buffer = bytes(self._buffer)
        self._buffer.clear()
        delimiter = b"--" + self.boundary
        for part in buffer.split(delimiter)[1:]:
            if part.startswith(b"--"):
                break
            part = part.strip(b"\r\n")
            if not part:
                continue
            self._callback("on_part_begin")
            header_bytes, separator, body = part.partition(b"\r\n\r\n")
            if not separator:
                continue
            for header in header_bytes.split(b"\r\n"):
                name, colon, value = header.partition(b":")
                if not colon:
                    continue
                value = value.strip()
                self._callback("on_header_field", name.strip(), 0, len(name.strip()))
                self._callback("on_header_value", value, 0, len(value))
                self._callback("on_header_end")
            self._callback("on_headers_finished")
            if body.endswith(b"\r\n"):
                body = body[:-2]
            self._callback("on_part_data", body, 0, len(body))
            self._callback("on_part_end")
        self._callback("on_end")

    def _callback(self, name: str, *args: object) -> None:
        callback = self.callbacks.get(name)
        if callback is not None:
            callback(*args)  # type: ignore[misc]


class QuerystringParser:
    def __init__(self, callbacks: dict[str, object]) -> None:
        self.callbacks = callbacks
        self._buffer = bytearray()

    def write(self, data: bytes) -> None:
        self._buffer.extend(data)

    def finalize(self) -> None:
        for name, value in parse_qsl(bytes(self._buffer).decode("latin-1"), keep_blank_values=True):
            self._callback("on_field_start")
            name_bytes = name.encode("latin-1")
            value_bytes = value.encode("latin-1")
            self._callback("on_field_name", name_bytes, 0, len(name_bytes))
            self._callback("on_field_data", value_bytes, 0, len(value_bytes))
            self._callback("on_field_end")
        self._callback("on_end")

    def _callback(self, name: str, *args: object) -> None:
        callback = self.callbacks.get(name)
        if callback is not None:
            callback(*args)  # type: ignore[misc]
