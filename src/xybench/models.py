"""Data models for xybench review system."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ReviewAction(str, Enum):
    """Actions a reviewer can take on AI-generated content."""

    APPROVE = "approve"
    REJECT = "reject"
    NEED_CHANGE = "need_change"
    NEW_IDEA = "new_idea"


class ReviewStatus(str, Enum):
    """Status of a review request."""

    PENDING = "pending"
    COMPLETED = "completed"
    REGENERATING = "regenerating"


@dataclass
class ReviewRequest:
    """A request for human review of AI-generated content."""

    content: Any
    session_id: str
    output_id: str = field(default_factory=lambda: f"gen_{uuid.uuid4().hex[:12]}")
    actions: list[ReviewAction] = field(
        default_factory=lambda: list(ReviewAction),
    )
    metadata: dict[str, Any] = field(default_factory=dict)
    notify: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_id": self.output_id,
            "session_id": self.session_id,
            "content": self.content,
            "actions": [a.value for a in self.actions],
            "metadata": self.metadata,
            "notify": self.notify,
            "status": ReviewStatus.PENDING.value,
            "created_at": self.created_at,
        }


@dataclass
class ReviewResult:
    """Result of a human review."""

    output_id: str
    action: ReviewAction
    reason: str = ""
    review_id: str = field(default_factory=lambda: f"rev_{uuid.uuid4().hex[:12]}")
    reviewed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "output_id": self.output_id,
            "action": self.action.value,
            "reason": self.reason,
            "reviewed_at": self.reviewed_at,
        }


@dataclass
class ReviewRecord:
    """Full record of a review, combining request and result."""

    output_id: str
    session_id: str
    content: Any
    actions: list[str]
    status: str
    created_at: str
    notify: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    review_id: str | None = None
    action: str | None = None
    reason: str | None = None
    reviewed_at: str | None = None
    new_content: Any = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "output_id": self.output_id,
            "session_id": self.session_id,
            "content": self.content,
            "actions": self.actions,
            "status": self.status,
            "created_at": self.created_at,
        }
        if self.notify:
            d["notify"] = self.notify
        if self.metadata:
            d["metadata"] = self.metadata
        if self.review_id:
            d["review_id"] = self.review_id
            d["action"] = self.action
            d["reason"] = self.reason
            d["reviewed_at"] = self.reviewed_at
        if self.new_content is not None:
            d["new_content"] = self.new_content
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReviewRecord:
        return cls(
            output_id=data["output_id"],
            session_id=data["session_id"],
            content=data["content"],
            actions=data["actions"],
            status=data["status"],
            created_at=data["created_at"],
            notify=data.get("notify"),
            metadata=data.get("metadata", {}),
            review_id=data.get("review_id"),
            action=data.get("action"),
            reason=data.get("reason"),
            reviewed_at=data.get("reviewed_at"),
            new_content=data.get("new_content"),
        )
