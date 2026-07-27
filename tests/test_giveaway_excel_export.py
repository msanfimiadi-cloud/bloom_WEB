from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import BytesIO

from openpyxl import Workbook

from app.api.v1.endpoints.admin import _excel_datetime


def test_giveaway_excel_datetime_is_openpyxl_compatible() -> None:
    source = datetime(2026, 7, 27, 10, 30, tzinfo=timezone(timedelta(hours=7)))

    exported = _excel_datetime(source)

    assert exported == datetime(2026, 7, 27, 3, 30)
    assert exported.tzinfo is None

    workbook = Workbook()
    workbook.active.append([exported])
    workbook.save(BytesIO())


def test_giveaway_excel_datetime_preserves_empty_and_naive_values() -> None:
    naive = datetime(2026, 7, 27, 10, 30)

    assert _excel_datetime(None) is None
    assert _excel_datetime(naive) is naive
