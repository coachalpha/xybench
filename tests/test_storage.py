"""Tests for xybench JSON storage backend."""

import json

import pytest

from xybench.models import ReviewAction, ReviewRecord, ReviewResult, ReviewStatus
from xybench.storage import JSONStorage


@pytest.fixture
def storage(tmp_path):
    return JSONStorage(tmp_path / "reviews")


@pytest.fixture
def sample_record():
    return ReviewRecord(
        output_id="gen_test123",
        session_id="session-001",
        content="AI-generated draft content",
        actions=["approve", "reject", "need_change"],
        status=ReviewStatus.PENDING.value,
        created_at="2024-01-01T00:00:00Z",
        notify="slack:#reviews",
    )


def test_save_and_load(storage, sample_record):
    storage.save(sample_record)
    loaded = storage.load(sample_record.output_id)
    assert loaded.output_id == sample_record.output_id
    assert loaded.content == sample_record.content
    assert loaded.status == ReviewStatus.PENDING.value


def test_save_creates_json_file(storage, sample_record):
    path = storage.save(sample_record)
    assert path.exists()
    assert path.suffix == ".json"
    data = json.loads(path.read_text())
    assert data["output_id"] == "gen_test123"


def test_load_not_found(storage):
    with pytest.raises(FileNotFoundError, match="Review not found"):
        storage.load("nonexistent")


def test_submit_review(storage, sample_record):
    storage.save(sample_record)

    result = ReviewResult(
        output_id="gen_test123",
        action=ReviewAction.APPROVE,
        reason="looks good",
    )
    updated = storage.submit_review(result)

    assert updated.status == ReviewStatus.COMPLETED.value
    assert updated.action == "approve"
    assert updated.reason == "looks good"
    assert updated.review_id is not None

    # Verify persisted
    reloaded = storage.load("gen_test123")
    assert reloaded.status == ReviewStatus.COMPLETED.value


def test_update_new_content(storage, sample_record):
    storage.save(sample_record)

    updated = storage.update_new_content("gen_test123", "revised content")
    assert updated.new_content == "revised content"
    assert updated.status == ReviewStatus.REGENERATING.value

    reloaded = storage.load("gen_test123")
    assert reloaded.new_content == "revised content"


def test_list_pending(storage):
    for i in range(3):
        record = ReviewRecord(
            output_id=f"gen_{i}",
            session_id="session-001",
            content=f"content {i}",
            actions=["approve"],
            status=ReviewStatus.PENDING.value if i < 2 else ReviewStatus.COMPLETED.value,
            created_at="2024-01-01T00:00:00Z",
        )
        storage.save(record)

    pending = storage.list_pending()
    assert len(pending) == 2


def test_list_pending_by_session(storage):
    for i, sid in enumerate(["s1", "s1", "s2"]):
        record = ReviewRecord(
            output_id=f"gen_{sid}_{i}",
            session_id=sid,
            content="content",
            actions=["approve"],
            status=ReviewStatus.PENDING.value,
            created_at="2024-01-01T00:00:00Z",
        )
        storage.save(record)

    pending = storage.list_pending(session_id="s1")
    assert len(pending) == 2


def test_list_all(storage):
    for i in range(3):
        record = ReviewRecord(
            output_id=f"gen_{i}",
            session_id="session-001",
            content=f"content {i}",
            actions=["approve"],
            status=ReviewStatus.PENDING.value,
            created_at="2024-01-01T00:00:00Z",
        )
        storage.save(record)

    all_records = storage.list_all()
    assert len(all_records) == 3
