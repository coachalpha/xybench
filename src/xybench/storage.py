"""JSON file-based storage for review records.

Each review is stored as a JSON file with the output_id as filename.
Zero external dependencies.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import ReviewRecord, ReviewResult, ReviewStatus


def _default_storage_dir() -> Path:
    return Path(os.environ.get("XYBENCH_STORAGE_DIR", "./reviews"))


class JSONStorage:
    """File-based JSON storage backend."""

    def __init__(self, storage_dir: str | Path | None = None) -> None:
        self.storage_dir = Path(storage_dir) if storage_dir else _default_storage_dir()
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, output_id: str) -> Path:
        return self.storage_dir / f"{output_id}.json"

    def save(self, record: ReviewRecord) -> Path:
        """Save a review record to disk."""
        path = self._path(record.output_id)
        path.write_text(json.dumps(record.to_dict(), indent=2, ensure_ascii=False))
        return path

    def load(self, output_id: str) -> ReviewRecord:
        """Load a review record by output_id."""
        path = self._path(output_id)
        if not path.exists():
            raise FileNotFoundError(f"Review not found: {output_id}")
        data = json.loads(path.read_text())
        return ReviewRecord.from_dict(data)

    def submit_review(self, result: ReviewResult) -> ReviewRecord:
        """Submit a review result and update the record."""
        record = self.load(result.output_id)
        record.review_id = result.review_id
        record.action = result.action.value
        record.reason = result.reason
        record.reviewed_at = result.reviewed_at
        record.status = ReviewStatus.COMPLETED.value
        self.save(record)
        return record

    def update_new_content(self, output_id: str, new_content: Any) -> ReviewRecord:
        """Update a record with regenerated content."""
        record = self.load(output_id)
        record.new_content = new_content
        record.status = ReviewStatus.REGENERATING.value
        self.save(record)
        return record

    def list_pending(self, session_id: str | None = None) -> list[ReviewRecord]:
        """List all pending review records, optionally filtered by session_id."""
        records = []
        for path in sorted(self.storage_dir.glob("*.json")):
            data = json.loads(path.read_text())
            if data.get("status") == ReviewStatus.PENDING.value:
                if session_id is None or data.get("session_id") == session_id:
                    records.append(ReviewRecord.from_dict(data))
        return records

    def list_all(self, session_id: str | None = None) -> list[ReviewRecord]:
        """List all review records, optionally filtered by session_id."""
        records = []
        for path in sorted(self.storage_dir.glob("*.json")):
            data = json.loads(path.read_text())
            if session_id is None or data.get("session_id") == session_id:
                records.append(ReviewRecord.from_dict(data))
        return records
