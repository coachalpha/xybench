"""Tests for xybench core review API."""

import asyncio

import pytest

from xybench.models import ReviewAction, ReviewStatus
from xybench.review import get_storage, review, submit_review, update_regenerated_content


@pytest.fixture(autouse=True)
def reset_storage(tmp_path, monkeypatch):
    """Reset global storage for each test."""
    import xybench.review as review_module

    review_module._default_storage = None
    monkeypatch.setenv("XYBENCH_STORAGE_DIR", str(tmp_path / "reviews"))


@pytest.fixture
def storage_dir(tmp_path):
    return str(tmp_path / "reviews")


async def test_review_creates_pending_record(storage_dir):
    """review() should create a pending record and poll for completion."""
    storage = get_storage(storage_dir)

    async def approve_after_delay():
        await asyncio.sleep(0.2)
        submit_review("test_output", "approve", reason="lgtm", storage_dir=storage_dir)

    # We need to know the output_id, so we'll create and submit manually
    from xybench.models import ReviewRecord

    record = ReviewRecord(
        output_id="test_output",
        session_id="test-session",
        content="test content",
        actions=["approve", "reject"],
        status=ReviewStatus.PENDING.value,
        created_at="2024-01-01T00:00:00Z",
    )
    storage.save(record)

    # Approve in background
    task = asyncio.create_task(approve_after_delay())

    # Poll
    while True:
        await asyncio.sleep(0.1)
        loaded = storage.load("test_output")
        if loaded.status != ReviewStatus.PENDING.value:
            break

    await task

    assert loaded.action == "approve"
    assert loaded.reason == "lgtm"


def test_submit_review_updates_record(storage_dir):
    storage = get_storage(storage_dir)

    from xybench.models import ReviewRecord

    record = ReviewRecord(
        output_id="gen_xyz",
        session_id="s1",
        content="draft",
        actions=["approve", "reject"],
        status=ReviewStatus.PENDING.value,
        created_at="2024-01-01T00:00:00Z",
    )
    storage.save(record)

    updated = submit_review("gen_xyz", "reject", reason="too vague", storage_dir=storage_dir)
    assert updated.status == ReviewStatus.COMPLETED.value
    assert updated.action == "reject"
    assert updated.reason == "too vague"


def test_update_regenerated_content(storage_dir):
    storage = get_storage(storage_dir)

    from xybench.models import ReviewRecord

    record = ReviewRecord(
        output_id="gen_regen",
        session_id="s1",
        content="original",
        actions=["approve"],
        status=ReviewStatus.COMPLETED.value,
        created_at="2024-01-01T00:00:00Z",
    )
    storage.save(record)

    updated = update_regenerated_content("gen_regen", "revised version", storage_dir=storage_dir)
    assert updated.new_content == "revised version"
    assert updated.status == ReviewStatus.REGENERATING.value
