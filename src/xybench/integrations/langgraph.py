"""LangGraph integration for xybench.

Provides a review node that can be inserted into any LangGraph workflow
to add human-in-the-loop review with minimal code.

Usage::

    from xybench.integrations.langgraph import create_review_node

    review_node = create_review_node(
        actions=["approve", "reject", "need_change"],
        notify="slack:#review-channel",
    )

    graph = StateGraph(AgentState)
    graph.add_node("generate", generate_node)
    graph.add_node("review", review_node)
    graph.add_node("regenerate", regenerate_node)

    graph.add_edge("generate", "review")
    graph.add_conditional_edges(
        "review",
        route_after_review,
        {"approve": END, "need_change": "regenerate", "reject": END},
    )
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable

from ..models import ReviewAction
from ..review import review as xybench_review
from ..review import update_regenerated_content


def create_review_node(
    *,
    content_key: str = "draft",
    session_key: str = "session_id",
    actions: list[str] | None = None,
    notify: str | None = None,
    storage_dir: str | None = None,
    poll_interval: float = 1.0,
) -> Callable[..., dict[str, Any]]:
    """Create a LangGraph node function for human review.

    The returned function reads content from the state, submits it for
    review, and returns the result merged back into the state.

    Args:
        content_key: State key containing the content to review.
        session_key: State key containing the session/thread id.
        actions: Allowed review actions.
        notify: Notification target (e.g. "slack:#channel").
        storage_dir: Override storage directory.
        poll_interval: Seconds between polling.

    Returns:
        A LangGraph-compatible node function.
    """

    async def _review_node(state: dict[str, Any]) -> dict[str, Any]:
        content = state[content_key]
        session_id = state.get(session_key, "default")

        result = await xybench_review(
            content=content,
            session_id=session_id,
            actions=actions,
            notify=notify,
            storage_dir=storage_dir,
            poll_interval=poll_interval,
        )

        return {
            "review_action": result.action.value,
            "review_reason": result.reason,
            "review_id": result.review_id,
            "output_id": result.output_id,
        }

    def review_node(state: dict[str, Any]) -> dict[str, Any]:
        """Sync wrapper for LangGraph compatibility."""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, _review_node(state)).result()
        return asyncio.run(_review_node(state))

    review_node.__name__ = "xybench_review"
    review_node.__doc__ = "Human-in-the-loop review node powered by xybench."
    return review_node


def route_after_review(state: dict[str, Any]) -> str:
    """Route function for conditional edges after a review node.

    Returns the review action string, which can be used as edge targets.
    """
    return state.get("review_action", "approve")
