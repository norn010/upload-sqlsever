from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import Any

import pandas as pd

REQUIRED_COLUMNS = ["business_key", "name", "amount", "record_date"]


@dataclass
class ValidationErrorItem:
    row_number: int
    column_name: str | None
    error_message: str


def parse_excel_bytes(file_bytes: bytes) -> pd.DataFrame:
    frame = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
    normalized = {col: str(col).strip().lower() for col in frame.columns}
    frame = frame.rename(columns=normalized)
    return frame


def validate_required_columns(frame: pd.DataFrame) -> list[str]:
    return [col for col in REQUIRED_COLUMNS if col not in frame.columns]


def validate_and_transform_rows(
    frame: pd.DataFrame,
) -> tuple[list[dict[str, Any]], list[ValidationErrorItem]]:
    valid_rows: list[dict[str, Any]] = []
    errors: list[ValidationErrorItem] = []

    for idx, row in frame.iterrows():
        row_number = idx + 2
        business_key = str(row.get("business_key", "")).strip()
        name = str(row.get("name", "")).strip()
        amount_value = row.get("amount")
        record_date_value = row.get("record_date")

        if not business_key:
            errors.append(
                ValidationErrorItem(
                    row_number=row_number,
                    column_name="business_key",
                    error_message="business_key is required",
                )
            )
        if not name:
            errors.append(
                ValidationErrorItem(
                    row_number=row_number,
                    column_name="name",
                    error_message="name is required",
                )
            )

        amount: Decimal | None = None
        try:
            amount = Decimal(str(amount_value))
        except (InvalidOperation, TypeError, ValueError):
            errors.append(
                ValidationErrorItem(
                    row_number=row_number,
                    column_name="amount",
                    error_message=f"amount is invalid: {amount_value}",
                )
            )

        parsed_date: date | None = None
        try:
            parsed_date = pd.to_datetime(record_date_value).date()
        except Exception:  # noqa: BLE001
            errors.append(
                ValidationErrorItem(
                    row_number=row_number,
                    column_name="record_date",
                    error_message=f"record_date is invalid: {record_date_value}",
                )
            )

        if any(error.row_number == row_number for error in errors):
            continue

        valid_rows.append(
            {
                "business_key": business_key,
                "name": name,
                "amount": amount,
                "record_date": parsed_date,
            }
        )

    return valid_rows, errors
