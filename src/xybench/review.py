"""Core review API for xybench.

This module provides the main `review()` function that developers call
from their AI pipelines to request human review.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from .models import ReviewAction, ReviewRecord, ReviewRequest, ReviewResult, ReviewStatus
from .notify import send_notification
from .storage import JSONStorage

logger = logging.getLogger(__name__)

_default_storage: JSONStorage | None = None


def get_storage(storage_dir: str | None = None) -> JSONStorage:
    """Get or create the default storage instance."""
    global _default_storage
    if _default_storage is None or storage_dir is not None:
        _default_storage = JSONStorage(storage_dir)
    return _default_storage


async def review(
    content: Any,
    session_id: str,
    *,
    actions: list[str] | None = None,
    notify: str | None = None,
    metadata: dict[str, Any] | None = None,
    storage_dir: str | None = None,
    poll_interval: float = 1.0,
) -> ReviewResult:
    """Submit content for human review and wait for the result.

    This is the primary API. It creates a review request, stores it,
    sends a notification, and polls until a reviewer submits their decision.

    Args:
        content: The AI-generated content to review. Can be any JSON-serializable value.
        session_id: Identifier for the current agent session / thread.
        actions: List of allowed actions. Defaults to all four actions.
        notify: Notification target. Format: "slack:#channel" or "email:user@example.com".
        metadata: Arbitrary metadata to attach to the review.
        storage_dir: Override the default storage directory.
        poll_interval: Seconds between polling for review completion.

    Returns:
        ReviewResult with the reviewer's action and reason.

    Example::

        from xybench import review

        result = await review(
            content=agent_output,
            session_id=thread_id,
            actions=["approve", "reject", "need_change", "new_idea"],
            notify="slack:#review-channel",
        )

        if result.action == "need_change":
            new_draft = agent.regenerate(
                original=agent_output,
                feedback=result.reason,
            )
    """
    action_enums = [ReviewAction(a) for a in (actions or ["approve", "reject", "need_change", "new_idea"])]

    request = ReviewRequest(
        content=content,
        session_id=session_id,
        actions=action_enums,
        notify=notify,
        metadata=metadata or {},
    )

    storage = get_storage(storage_dir)

    record = ReviewRecord(
        output_id=request.output_id,
        session_id=request.session_id,
        content=request.content,
        actions=[a.value for a in request.actions],
        status=ReviewStatus.PENDING.value,
        created_at=request.created_at,
        notify=request.notify,
        metadata=request.metadata,
    )
    storage.save(record)
    logger.info("Review created: %s (session=%s)", record.output_id, session_id)

    await send_notification(record)

    # Poll until a reviewer submits their decision
    while True:
        await asyncio.sleep(poll_interval)
        record = storage.load(request.output_id)
        if record.status != ReviewStatus.PENDING.value:
            break

    return ReviewResult(
        output_id=record.output_id,
        action=ReviewAction(record.action),
        reason=record.reason or "",
        review_id=record.review_id or "",
        reviewed_at=record.reviewed_at or "",
    )


def submit_review(
    output_id: str,
    action: str,
    reason: str = "",
    *,
    storage_dir: str | None = None,
) -> ReviewRecord:
    """Submit a review decision (called by the reviewer UI).

    Args:
        output_id: The output_id of the review to submit.
        action: One of "approve", "reject", "need_change", "new_idea".
        reason: The reviewer's reason / feedback.
        storage_dir: Override the default storage directory.

    Returns:
        Updated ReviewRecord.
    """
    storage = get_storage(storage_dir)
    result = ReviewResult(
        output_id=output_id,
        action=ReviewAction(action),
        reason=reason,
    )
    return storage.submit_review(result)


def update_regenerated_content(
    output_id: str,
    new_content: Any,
    *,
    storage_dir: str | None = None,
) -> ReviewRecord:
    """Update a review record with regenerated content for comparison.

    Args:
        output_id: The output_id of the original review.
        new_content: The regenerated content.
        storage_dir: Override the default storage directory.

    Returns:
        Updated ReviewRecord with new_content and status="regenerating".
    """
    storage = get_storage(storage_dir)
    return storage.update_new_content(output_id, new_content)
