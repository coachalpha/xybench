"""xybench - Eval framework for AI applications, starting with HITL.

Usage::

    from xybench import review

    result = await review(
        content=agent_output,
        session_id=thread_id,
        actions=["approve", "reject", "need_change", "new_idea"],
        notify="slack:#review-channel",
    )
"""

from .models import ReviewAction, ReviewRecord, ReviewResult, ReviewStatus
from .review import review, submit_review, update_regenerated_content
from .storage import JSONStorage

__version__ = "0.1.0"

__all__ = [
    "ReviewAction",
    "ReviewRecord",
    "ReviewResult",
    "ReviewStatus",
    "JSONStorage",
    "review",
    "submit_review",
    "update_regenerated_content",
]
