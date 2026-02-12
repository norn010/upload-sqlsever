from datetime import date
from decimal import Decimal
from io import BytesIO

import pandas as pd

from app.services.excel_service import (
    parse_excel_bytes,
    validate_and_transform_rows,
    validate_required_columns,
)


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
    assert valid[0]["invoice_no"] is None
    assert valid[0]["group_id"] is None
    assert len(errors) == 3


def test_parse_excel_bytes_maps_finance_screening_format() -> None:
    source = pd.DataFrame(
        [
            {
                "doc_date": "2026-01-28",
                "invoice_no": "INV-001",
                "customer_name": "Alice",
                "item": "X",
                "gross": 1000,
                "tax": 70,
                "total": 1070,
                "vin": "VIN001",
                "cancel_flag": None,
                "cancel_gross": 0,
                "cancel_tax": 0,
                "cancel_total": 0,
                "tax_branch": "X",
                "tax_sub_branch": 0,
                "citizen_id": "123",
                "sale_price": 1070,
                "com_fn": 1000,
                "com": 70,
                "rule_applied": "finance_sent",
                "is_duplicate_tank": False,
                "group_id": "TANK::VIN001",
            }
        ]
    )
    buffer = BytesIO()
    source.to_excel(buffer, index=False)

    parsed = parse_excel_bytes(buffer.getvalue())
    assert set(["business_key", "name", "amount", "record_date"]).issubset(parsed.columns)
    assert "group_id" in parsed.columns
    assert "sale_price" in parsed.columns
    assert parsed.loc[0, "business_key"] == "TANK::VIN001"
    assert parsed.loc[0, "name"] == "Alice"
    assert str(parsed.loc[0, "amount"]) == "1070"


def test_parse_excel_bytes_maps_finance_screening_thai_headers() -> None:
    source = pd.DataFrame(
        [
            {
                "วันที่ใบกำกับ": "2026-02-10",
                "เลขที่ใบกำกับ": "INV-TH-001",
                "ชื่อ-นามสกุล": "สมชาย ใจดี",
                "รายการ": "รถยนต์",
                "มูลค่าสินค้า": 250000,
                "ภาษี": 17500,
                "มูลค่ารวม": 267500,
                "เลขตัวถัง": "VINTH001",
                "ยกเลิก": None,
                "มูลค่าสินค้ายกเลิก": 0,
                "ภาษียกเลิก": 0,
                "มูลค่ารวมยกเลิก": 0,
                "ประเภทองค์กร สนญ.": "X",
                "ประเภทองค์กร สาขาที่": 0,
                "เลขประจำตัวผู้เสียภาษี": "'0101234567890",
                "ราคาขาย": 267500,
                "COM F/N": 250000,
                "COM": 17500,
                "rule_applied": "finance_sent",
                "is_duplicate_tank": False,
                "group_id": "TANK::VINTH001",
            }
        ]
    )
    buffer = BytesIO()
    source.to_excel(buffer, index=False)

    parsed = parse_excel_bytes(buffer.getvalue())
    assert parsed.loc[0, "business_key"] == "TANK::VINTH001"
    assert parsed.loc[0, "name"] == "สมชาย ใจดี"
    assert str(parsed.loc[0, "amount"]) == "267500"
    assert parsed.loc[0, "taxpayer_id"] == "'0101234567890"
    assert str(pd.to_datetime(parsed.loc[0, "record_date"]).date()) == "2026-02-10"
