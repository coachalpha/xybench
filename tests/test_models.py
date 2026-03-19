"""Tests for xybench data models."""

from xybench.models import (
    ReviewAction,
    ReviewRecord,
    ReviewRequest,
    ReviewResult,
    ReviewStatus,
)


def test_review_action_values():
    assert ReviewAction.APPROVE.value == "approve"
    assert ReviewAction.REJECT.value == "reject"
    assert ReviewAction.NEED_CHANGE.value == "need_change"
    assert ReviewAction.NEW_IDEA.value == "new_idea"


def test_review_request_defaults():
    req = ReviewRequest(content="hello", session_id="s1")
    assert req.content == "hello"
    assert req.session_id == "s1"
    assert req.output_id.startswith("gen_")
    assert len(req.actions) == 4
    assert req.metadata == {}


def test_review_request_to_dict():
    req = ReviewRequest(content="test", session_id="s1")
    d = req.to_dict()
    assert d["content"] == "test"
    assert d["session_id"] == "s1"
    assert d["status"] == "pending"
    assert "created_at" in d


def test_review_result_to_dict():
    result = ReviewResult(output_id="gen_abc", action=ReviewAction.APPROVE, reason="looks good")
    d = result.to_dict()
    assert d["output_id"] == "gen_abc"
    assert d["action"] == "approve"
    assert d["reason"] == "looks good"
    assert d["review_id"].startswith("rev_")


def test_review_record_roundtrip():
    record = ReviewRecord(
        output_id="gen_abc",
        session_id="s1",
        content="test content",
        actions=["approve", "reject"],
        status="pending",
        created_at="2024-01-01T00:00:00Z",
    )
    d = record.to_dict()
    restored = ReviewRecord.from_dict(d)
    assert restored.output_id == record.output_id
    assert restored.content == record.content
    assert restored.status == record.status


def test_review_record_with_review():
    record = ReviewRecord(
        output_id="gen_abc",
        session_id="s1",
        content="test",
        actions=["approve"],
        status="completed",
        created_at="2024-01-01T00:00:00Z",
        review_id="rev_123",
        action="approve",
        reason="lgtm",
        reviewed_at="2024-01-01T01:00:00Z",
    )
    d = record.to_dict()
    assert d["review_id"] == "rev_123"
    assert d["action"] == "approve"


def test_review_record_with_new_content():
    record = ReviewRecord(
        output_id="gen_abc",
        session_id="s1",
        content="original",
        actions=["approve"],
        status="regenerating",
        created_at="2024-01-01T00:00:00Z",
        new_content="revised",
    )
    d = record.to_dict()
    assert d["new_content"] == "revised"
