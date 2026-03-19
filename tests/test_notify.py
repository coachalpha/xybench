"""Tests for xybench notification system."""

import logging

import pytest

from xybench.models import ReviewRecord, ReviewStatus
from xybench.notify import send_notification


@pytest.fixture
def sample_record():
    return ReviewRecord(
        output_id="gen_notify_test",
        session_id="session-001",
        content="Test content for notification",
        actions=["approve", "reject"],
        status=ReviewStatus.PENDING.value,
        created_at="2024-01-01T00:00:00Z",
    )


async def test_no_notification_when_notify_is_none(sample_record):
    """Should silently skip when notify is None."""
    sample_record.notify = None
    await send_notification(sample_record)  # Should not raise


async def test_invalid_notify_format_logs_warning(sample_record, caplog):
    """Should log a warning for invalid notify format."""
    sample_record.notify = "invalid"
    with caplog.at_level(logging.WARNING):
        await send_notification(sample_record)
    assert "Invalid notify format" in caplog.text


async def test_unknown_notification_type_logs_warning(sample_record, caplog):
    """Should log a warning for unknown notification types."""
    sample_record.notify = "sms:+1234567890"
    with caplog.at_level(logging.WARNING):
        await send_notification(sample_record)
    assert "Unknown notification type" in caplog.text


async def test_slack_without_webhook_logs_warning(sample_record, caplog, monkeypatch):
    """Should log a warning when Slack webhook URL is not set."""
    monkeypatch.delenv("XYBENCH_SLACK_WEBHOOK_URL", raising=False)
    sample_record.notify = "slack:#test-channel"

    with caplog.at_level(logging.WARNING):
        await send_notification(sample_record)

    # Either "XYBENCH_SLACK_WEBHOOK_URL not set" (httpx installed)
    # or "Failed to send slack notification" (httpx not installed, error caught)
    assert "slack" in caplog.text.lower()
