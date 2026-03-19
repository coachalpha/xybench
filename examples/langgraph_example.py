"""LangGraph integration example: AI agent with human-in-the-loop review.

This example shows how to add xybench review to a LangGraph workflow.

Requirements:
    pip install xybench[langgraph]
"""

from __future__ import annotations

from typing import Any, TypedDict

from xybench.integrations.langgraph import create_review_node, route_after_review


class AgentState(TypedDict, total=False):
    topic: str
    draft: str
    session_id: str
    review_action: str
    review_reason: str
    review_id: str
    output_id: str
    final_output: str


def generate(state: AgentState) -> dict[str, Any]:
    """Generate a draft (simulated LLM call)."""
    topic = state.get("topic", "AI trends")
    draft = (
        f"# Report: {topic}\n\n"
        f"This is an AI-generated report about {topic}. "
        f"Key findings include increased adoption across industries "
        f"and growing investment in infrastructure."
    )
    return {"draft": draft}


def regenerate(state: AgentState) -> dict[str, Any]:
    """Regenerate content based on review feedback."""
    feedback = state.get("review_reason", "")
    original = state.get("draft", "")
    new_draft = f"[Revised: {feedback}]\n\n{original}\n\n[Additional details based on feedback]"

    from xybench import update_regenerated_content

    output_id = state.get("output_id", "")
    if output_id:
        update_regenerated_content(output_id, new_draft)

    return {"draft": new_draft}


def finalize(state: AgentState) -> dict[str, Any]:
    """Finalize the approved content."""
    return {"final_output": state["draft"]}


# Build the graph
review_node = create_review_node(
    content_key="draft",
    session_key="session_id",
    actions=["approve", "reject", "need_change"],
    # notify="slack:#review-channel",
)


def build_graph() -> Any:
    """Build and return the LangGraph workflow."""
    try:
        from langgraph.graph import END, StateGraph
    except ImportError:
        raise ImportError(
            "langgraph is required for this example. "
            "Install it with: pip install xybench[langgraph]"
        )

    graph = StateGraph(AgentState)

    graph.add_node("generate", generate)
    graph.add_node("review", review_node)
    graph.add_node("regenerate", regenerate)
    graph.add_node("finalize", finalize)

    graph.set_entry_point("generate")
    graph.add_edge("generate", "review")
    graph.add_conditional_edges(
        "review",
        route_after_review,
        {
            "approve": "finalize",
            "need_change": "regenerate",
            "reject": END,
        },
    )
    graph.add_edge("regenerate", "review")
    graph.add_edge("finalize", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({
        "topic": "Q3 AI Infrastructure Trends",
        "session_id": "langgraph-demo-001",
    })
    print("Final result:", result)
