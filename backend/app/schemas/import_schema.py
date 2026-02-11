from datetime import datetime

from pydantic import BaseModel


class ImportErrorItem(BaseModel):
    row_number: int
    column_name: str | None = None
    error_message: str


class ImportResult(BaseModel):
    job_id: int
    status: str
    filename: str
    total_rows: int
    imported_rows: int
    failed_rows: int
    message: str | None = None
    errors: list[ImportErrorItem] = []


class ImportJobResponse(BaseModel):
    id: int
    correlation_id: str
    filename: str
    status: str
    total_rows: int
    imported_rows: int
    failed_rows: int
    message: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
