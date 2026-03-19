"""Notification backends for xybench.

Supports Slack webhooks and email (SMTP). Notifications are fire-and-forget
and never block the review flow on failure.
"""

from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import ReviewRecord

logger = logging.getLogger(__name__)


async def send_notification(record: ReviewRecord) -> None:
    """Dispatch notification based on the record's notify field.

    Format: "slack:#channel" or "email:user@example.com"
    """
    if not record.notify:
        return

    kind, _, target = record.notify.partition(":")
    if not target:
        logger.warning("Invalid notify format: %s (expected 'slack:#channel' or 'email:addr')", record.notify)
        return

    try:
        if kind == "slack":
            await _send_slack(target, record)
        elif kind == "email":
            await _send_email(target, record)
        else:
            logger.warning("Unknown notification type: %s", kind)
    except Exception:
        logger.exception("Failed to send %s notification for %s", kind, record.output_id)


async def _send_slack(channel: str, record: ReviewRecord) -> None:
    """Send a Slack notification via incoming webhook."""
    try:
        import httpx
    except ImportError:
        raise ImportError(
            "httpx is required for Slack notifications. "
            "Install it with: pip install xybench[slack]"
        )

    webhook_url = os.environ.get("XYBENCH_SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("XYBENCH_SLACK_WEBHOOK_URL not set, skipping Slack notification")
        return

    content_preview = str(record.content)[:200]
    message = {
        "channel": channel,
        "text": f"New review pending: *{record.output_id}*",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*New review pending*\n"
                    f"Output: `{record.output_id}`\n"
                    f"Session: `{record.session_id}`\n"
                    f"Preview: {content_preview}...",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": action.title()},
                        "value": action,
                    }
                    for action in record.actions
                ],
            },
        ],
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(webhook_url, json=message)
        resp.raise_for_status()
    logger.info("Slack notification sent for %s", record.output_id)


async def _send_email(to_addr: str, record: ReviewRecord) -> None:
    """Send an email notification via SMTP."""
    host = os.environ.get("XYBENCH_SMTP_HOST", "localhost")
    port = int(os.environ.get("XYBENCH_SMTP_PORT", "587"))
    user = os.environ.get("XYBENCH_SMTP_USER", "")
    password = os.environ.get("XYBENCH_SMTP_PASSWORD", "")
    from_addr = os.environ.get("XYBENCH_SMTP_FROM", user)

    content_preview = str(record.content)[:500]

    msg = EmailMessage()
    msg["Subject"] = f"[xybench] Review pending: {record.output_id}"
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(
        f"A new review is pending.\n\n"
        f"Output ID: {record.output_id}\n"
        f"Session: {record.session_id}\n\n"
        f"Content preview:\n{content_preview}\n\n"
        f"Actions available: {', '.join(record.actions)}\n"
    )

    with smtplib.SMTP(host, port) as server:
        if user and password:
            server.starttls()
            server.login(user, password)
        server.send_message(msg)
    logger.info("Email notification sent to %s for %s", to_addr, record.output_id)
