from datetime import date
from decimal import Decimal

import pandas as pd

from app.services.excel_service import validate_and_transform_rows, validate_required_columns


def test_validate_required_columns_reports_missing() -> None:
    frame = pd.DataFrame({"business_key": ["A-001"], "name": ["Alice"]})
    missing = validate_required_columns(frame)
    assert missing == ["amount", "record_date"]


def test_validate_and_transform_rows_splits_valid_and_invalid() -> None:
    frame = pd.DataFrame(
        [
            {"business_key": "A-001", "name": "Alice", "amount": "25.50", "record_date": "2025-01-12"},
            {"business_key": "", "name": "Bob", "amount": "abc", "record_date": "bad-date"},
        ]
    )

    valid, errors = validate_and_transform_rows(frame)

    assert len(valid) == 1
    assert valid[0]["business_key"] == "A-001"
    assert valid[0]["amount"] == Decimal("25.50")
    assert valid[0]["record_date"] == date(2025, 1, 12)
    assert len(errors) == 3
