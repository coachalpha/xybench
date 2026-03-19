"""Basic example: submit content for human review and wait for the result.

Run this script, then use the Streamlit reviewer app to submit a decision:

    # Terminal 1: run the agent
    python examples/basic_review.py

    # Terminal 2: run the reviewer UI
    streamlit run examples/reviewer_app.py
"""

import asyncio

from xybench import review


async def main() -> None:
    agent_output = (
        "## Q3 Marketing Report\n\n"
        "Revenue increased 23% QoQ driven by the new product launch. "
        "Customer acquisition cost decreased by 15% due to organic growth. "
        "Recommendation: increase ad spend by 30% in Q4 to capitalize on momentum."
    )

    print(f"Agent generated content:\n{agent_output}\n")
    print("Waiting for human review...")

    result = await review(
        content=agent_output,
        session_id="demo-session-001",
        actions=["approve", "reject", "need_change", "new_idea"],
        # Uncomment to enable Slack notifications:
        # notify="slack:#review-channel",
    )

    print(f"\nReview received!")
    print(f"  Action: {result.action.value}")
    print(f"  Reason: {result.reason}")

    if result.action.value == "need_change":
        print("\nRegenerating with feedback...")
        new_draft = f"[Revised based on feedback: {result.reason}]\n\n{agent_output}"

        from xybench import update_regenerated_content

        update_regenerated_content(result.output_id, new_draft)
        print("New draft saved. Reviewer can now see the comparison view.")


if __name__ == "__main__":
    asyncio.run(main())
