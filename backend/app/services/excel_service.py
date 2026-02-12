from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import Any

import pandas as pd

REQUIRED_COLUMNS = ["business_key", "name", "amount", "record_date"]
FINANCE_SCREENING_ALIASES: dict[str, list[str]] = {
    "business_key": ["business_key", "group_id", "เลขตัวถัง", "เลขที่ใบกำกับ"],
    "name": ["name", "ชื่อ-นามสกุล"],
    "amount": ["amount", "ราคาขาย", "มูลค่ารวม", "มูลค่าสินค้า"],
    "record_date": ["record_date", "วันที่ใบกำกับ"],
    "invoice_date": ["invoice_date", "วันที่ใบกำกับ"],
    "invoice_no": ["invoice_no", "เลขที่ใบกำกับ"],
    "item_description": ["item_description", "รายการ"],
    "product_value": ["product_value", "มูลค่าสินค้า"],
    "tax_value": ["tax_value", "ภาษี"],
    "total_value": ["total_value", "มูลค่ารวม"],
    "vin_no": ["vin_no", "เลขตัวถัง"],
    "cancel_flag": ["cancel_flag", "ยกเลิก"],
    "cancel_product_value": ["cancel_product_value", "มูลค่าสินค้ายกเลิก"],
    "cancel_tax_value": ["cancel_tax_value", "ภาษียกเลิก"],
    "cancel_total_value": ["cancel_total_value", "มูลค่ารวมยกเลิก"],
    "org_type_hq": ["org_type_hq", "ประเภทองค์กร สนญ."],
    "org_type_branch_no": ["org_type_branch_no", "ประเภทองค์กร สาขาที่"],
    "taxpayer_id": ["taxpayer_id", "เลขประจำตัวผู้เสียภาษี"],
    "sale_price": ["sale_price", "ราคาขาย"],
    "com_fn": ["com_fn", "com f/n"],
    "com_value": ["com_value", "com"],
    "rule_applied": ["rule_applied"],
    "is_duplicate_tank": ["is_duplicate_tank"],
    "group_id": ["group_id"],
}


@dataclass
class ValidationErrorItem:
    row_number: int
    column_name: str | None
    error_message: str


def _as_clean_string(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none"}:
        return ""
    return text


def _coalesce_columns(frame: pd.DataFrame, candidates: list[str]) -> pd.Series:
    result = pd.Series([""] * len(frame), index=frame.index, dtype="object")
    for col in candidates:
        if col not in frame.columns:
            continue
        values = frame[col].map(_as_clean_string)
        mask = (result == "") & (values != "")
        result.loc[mask] = values.loc[mask]
    return result


def _coalesce_raw_columns(frame: pd.DataFrame, candidates: list[str]) -> pd.Series:
    result = pd.Series([None] * len(frame), index=frame.index, dtype="object")
    for col in candidates:
        if col not in frame.columns:
            continue
        values = frame[col]
        mask = result.isna() & values.notna()
        result.loc[mask] = values.loc[mask]
    return result


def _parse_optional_decimal(value: Any) -> Decimal | None:
    text = _as_clean_string(value).replace(",", "")
    if text == "":
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def _parse_optional_date(value: Any) -> date | None:
    if pd.isna(value):
        return None
    text = _as_clean_string(value)
    if text == "":
        return None
    return pd.to_datetime(value).date()


def _parse_optional_int(value: Any) -> int | None:
    text = _as_clean_string(value)
    if text == "":
        return None
    return int(float(text))


def _parse_optional_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = _as_clean_string(value).lower()
    if text == "":
        return None
    if text in {"true", "1", "y", "yes"}:
        return True
    if text in {"false", "0", "n", "no"}:
        return False
    return None


def _map_finance_screening_format(frame: pd.DataFrame) -> pd.DataFrame:
    # `finance-screening-output.xlsx` may come with Thai or English headers.
    if "group_id" not in frame.columns and "วันที่ใบกำกับ" not in frame.columns:
        return frame

    columns = list(frame.columns)
    date_col = columns[0] if len(columns) > 0 else ""
    invoice_col = columns[1] if len(columns) > 1 else ""
    name_col = columns[2] if len(columns) > 2 else ""
    vin_col = columns[7] if len(columns) > 7 else ""
    sale_price_col = columns[15] if len(columns) > 15 else ""
    total_col = columns[6] if len(columns) > 6 else ""
    gross_col = columns[4] if len(columns) > 4 else ""

    mapped = pd.DataFrame(index=frame.index)
    mapped["business_key"] = _coalesce_columns(
        frame, FINANCE_SCREENING_ALIASES["business_key"] + [vin_col, invoice_col]
    )
    mapped["name"] = _coalesce_columns(frame, FINANCE_SCREENING_ALIASES["name"] + [name_col])
    mapped["amount"] = _coalesce_columns(
        frame, FINANCE_SCREENING_ALIASES["amount"] + [sale_price_col, total_col, gross_col]
    )
    mapped["record_date"] = _coalesce_raw_columns(
        frame, FINANCE_SCREENING_ALIASES["record_date"] + [date_col]
    )
    mapped["invoice_date"] = _coalesce_raw_columns(
        frame, FINANCE_SCREENING_ALIASES["invoice_date"] + [date_col]
    )
    mapped["invoice_no"] = _coalesce_columns(
        frame, FINANCE_SCREENING_ALIASES["invoice_no"] + [invoice_col]
    )
    mapped["item_description"] = _coalesce_columns(frame, FINANCE_SCREENING_ALIASES["item_description"])
    mapped["product_value"] = _coalesce_raw_columns(
        frame, FINANCE_SCREENING_ALIASES["product_value"] + [gross_col]
    )
    mapped["tax_value"] = _coalesce_raw_columns(frame, FINANCE_SCREENING_ALIASES["tax_value"])
    mapped["total_value"] = _coalesce_raw_columns(
        frame, FINANCE_SCREENING_ALIASES["total_value"] + [total_col]
    )
    mapped["vin_no"] = _coalesce_columns(frame, FINANCE_SCREENING_ALIASES["vin_no"] + [vin_col])
    mapped["cancel_flag"] = _coalesce_columns(frame, FINANCE_SCREENING_ALIASES["cancel_flag"])
    mapped["cancel_product_value"] = _coalesce_raw_columns(
        frame, FINANCE_SCREENING_ALIASES["cancel_product_value"]
    )
    mapped["cancel_tax_value"] = _coalesce_raw_columns(
        frame, FINANCE_SCREENING_ALIASES["cancel_tax_value"]
    )
    mapped["cancel_total_value"] = _coalesce_raw_columns(
        frame, FINANCE_SCREENING_ALIASES["cancel_total_value"]
    )
    mapped["org_type_hq"] = _coalesce_columns(frame, FINANCE_SCREENING_ALIASES["org_type_hq"])
    mapped["org_type_branch_no"] = _coalesce_raw_columns(
        frame, FINANCE_SCREENING_ALIASES["org_type_branch_no"]
    )
    mapped["taxpayer_id"] = _coalesce_columns(frame, FINANCE_SCREENING_ALIASES["taxpayer_id"])
    mapped["sale_price"] = _coalesce_raw_columns(
        frame, FINANCE_SCREENING_ALIASES["sale_price"] + [sale_price_col]
    )
    mapped["com_fn"] = _coalesce_raw_columns(frame, FINANCE_SCREENING_ALIASES["com_fn"])
    mapped["com_value"] = _coalesce_raw_columns(frame, FINANCE_SCREENING_ALIASES["com_value"])
    mapped["rule_applied"] = _coalesce_columns(frame, FINANCE_SCREENING_ALIASES["rule_applied"])
    mapped["is_duplicate_tank"] = _coalesce_raw_columns(
        frame, FINANCE_SCREENING_ALIASES["is_duplicate_tank"]
    )
    mapped["group_id"] = _coalesce_columns(frame, FINANCE_SCREENING_ALIASES["group_id"])
    return mapped


def parse_excel_bytes(file_bytes: bytes) -> pd.DataFrame:
    frame = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
    normalized = {col: str(col).strip().lower() for col in frame.columns}
    frame = frame.rename(columns=normalized)
    if not set(REQUIRED_COLUMNS).issubset(frame.columns):
        frame = _map_finance_screening_format(frame)
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
        business_key = _as_clean_string(row.get("business_key"))
        name = _as_clean_string(row.get("name"))
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
            amount = Decimal(_as_clean_string(amount_value).replace(",", ""))
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
                "invoice_date": _parse_optional_date(row.get("invoice_date")),
                "invoice_no": _as_clean_string(row.get("invoice_no")) or None,
                "item_description": _as_clean_string(row.get("item_description")) or None,
                "product_value": _parse_optional_decimal(row.get("product_value")),
                "tax_value": _parse_optional_decimal(row.get("tax_value")),
                "total_value": _parse_optional_decimal(row.get("total_value")),
                "vin_no": _as_clean_string(row.get("vin_no")) or None,
                "cancel_flag": _as_clean_string(row.get("cancel_flag")) or None,
                "cancel_product_value": _parse_optional_decimal(row.get("cancel_product_value")),
                "cancel_tax_value": _parse_optional_decimal(row.get("cancel_tax_value")),
                "cancel_total_value": _parse_optional_decimal(row.get("cancel_total_value")),
                "org_type_hq": _as_clean_string(row.get("org_type_hq")) or None,
                "org_type_branch_no": _parse_optional_int(row.get("org_type_branch_no")),
                "taxpayer_id": _as_clean_string(row.get("taxpayer_id")).lstrip("'") or None,
                "sale_price": _parse_optional_decimal(row.get("sale_price")),
                "com_fn": _parse_optional_decimal(row.get("com_fn")),
                "com_value": _parse_optional_decimal(row.get("com_value")),
                "rule_applied": _as_clean_string(row.get("rule_applied")) or None,
                "is_duplicate_tank": _parse_optional_bool(row.get("is_duplicate_tank")),
                "group_id": _as_clean_string(row.get("group_id")) or None,
            }
        )

    return valid_rows, errors
