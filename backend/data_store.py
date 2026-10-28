"""Data handling: load and validate reports.

Reports are read from data/reports.json and checked with a Pydantic model.
If a record is missing a field or has an invalid priority, loading stops
with a clear error instead of failing later inside an endpoint.
"""
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

DATA_FILE = Path(__file__).parent / "data" / "reports.json"


class Report(BaseModel):
    id: int
    title: str = Field(min_length=1)
    category: str = Field(min_length=1)
    location: str = Field(min_length=1)
    source: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    priority: Literal["High", "Medium", "Low"]


def load_reports(path: Path = DATA_FILE) -> list[dict]:
    """Read the JSON file, validate every record, and return plain dicts."""
    with open(path, encoding="utf-8") as file:
        raw_reports = json.load(file)

    reports = [Report(**item) for item in raw_reports]

    ids = [report.id for report in reports]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate report id found in reports.json")

    return [report.model_dump() for report in reports]
