"""Streamlit review components for xybench.

Provides ReviewComponent (for reviewers to judge AI output) and
ComparisonView (to compare original vs regenerated content).

Usage::

    from xybench.streamlit import ReviewComponent

    ReviewComponent(session_id=st.query_params["id"])
"""

from __future__ import annotations

from typing import Any

from ..models import ReviewAction, ReviewStatus
from ..review import get_storage, submit_review


def ReviewComponent(
    session_id: str | None = None,
    output_id: str | None = None,
    storage_dir: str | None = None,
) -> None:
    """Render a review UI for pending reviews.

    Shows the AI-generated content and action buttons. When a reviewer
    submits their decision, the review record is updated.

    Args:
        session_id: Show reviews for this session. If None, shows all pending.
        output_id: Show a specific review by output_id.
        storage_dir: Override storage directory.
    """
    try:
        import streamlit as st
    except ImportError:
        raise ImportError(
            "streamlit is required for the review UI. "
            "Install it with: pip install xybench[streamlit]"
        )

    storage = get_storage(storage_dir)

    if output_id:
        try:
            record = storage.load(output_id)
            _render_single_review(st, record, storage_dir)
        except FileNotFoundError:
            st.error(f"Review not found: {output_id}")
        return

    pending = storage.list_pending(session_id)
    if not pending:
        st.info("No pending reviews.")
        return

    for record in pending:
        _render_single_review(st, record, storage_dir)
        st.divider()


def _render_single_review(st: Any, record: Any, storage_dir: str | None) -> None:
    """Render a single review card."""
    st.subheader(f"Review: {record.output_id}")
    st.caption(f"Session: {record.session_id} | Created: {record.created_at}")

    if record.status == ReviewStatus.COMPLETED.value:
        st.success(f"Reviewed: {record.action} — {record.reason}")
        return

    if record.new_content is not None:
        ComparisonView(record.content, record.new_content)
    else:
        st.markdown("**Content to review:**")
        if isinstance(record.content, str):
            st.text_area("Content", record.content, height=200, disabled=True, key=f"content_{record.output_id}")
        else:
            st.json(record.content)

    cols = st.columns(len(record.actions))
    action_labels = {
        "approve": "Approve",
        "reject": "Reject",
        "need_change": "Need Change",
        "new_idea": "New Idea",
    }

    reason = st.text_input("Reason / feedback:", key=f"reason_{record.output_id}")

    for i, action in enumerate(record.actions):
        label = action_labels.get(action, action.title())
        if cols[i].button(label, key=f"{action}_{record.output_id}"):
            submit_review(
                output_id=record.output_id,
                action=action,
                reason=reason,
                storage_dir=storage_dir,
            )
            st.success(f"Feedback submitted: **{label}**. The AI is processing your feedback.")
            st.rerun()


def ComparisonView(
    original: Any,
    regenerated: Any,
) -> None:
    """Render a side-by-side comparison of original vs regenerated content.

    Args:
        original: The original AI-generated content.
        regenerated: The regenerated content after feedback.
    """
    try:
        import streamlit as st
    except ImportError:
        raise ImportError(
            "streamlit is required for the comparison view. "
            "Install it with: pip install xybench[streamlit]"
        )

    st.markdown("**Original vs Regenerated:**")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Original**")
        if isinstance(original, str):
            st.text_area("Original", original, height=300, disabled=True, key="cmp_original")
        else:
            st.json(original)

    with col2:
        st.markdown("**Regenerated**")
        if isinstance(regenerated, str):
            st.text_area("Regenerated", regenerated, height=300, disabled=True, key="cmp_regenerated")
        else:
            st.json(regenerated)
