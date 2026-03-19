# xybench

**Eval framework for AI applications, starting with human-in-the-loop (HITL).**

> Turn the informal "AI generates → human reviews → AI regenerates" loop into a structured, trackable, iterable system.

## Why

Building agentic AI apps? You'll hit these problems:

1. **No clear way to judge AI output quality** across your team
2. **HITL review flows require building UI, state management, notifications** from scratch
3. **Human feedback doesn't feed back** into improving AI behavior

xybench solves this by treating **HITL as a special case of eval** — every review naturally produces structured data that can later train LLM judges, improve prompts, and track quality over time.

## Features

- **2 lines to integrate** — `from xybench import review` + `await review(content, session_id)`
- **Reviewer UI** — Streamlit components for non-technical reviewers
- **Comparison view** — Side-by-side original vs regenerated content
- **Notifications** — Slack webhooks and email out of the box
- **LangGraph integration** — Drop-in review node for LangGraph workflows
- **Local-first** — JSON file storage, zero infrastructure, data never leaves your network
- **Apache 2.0** — Enterprise-friendly license

## Quickstart

### Install

```bash
pip install xybench
```

With optional integrations:

```bash
pip install xybench[langgraph]     # LangGraph support
pip install xybench[streamlit]     # Reviewer UI
pip install xybench[slack]         # Slack notifications
pip install xybench[all]           # Everything
```

### Add review to your AI pipeline

```python
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
```

### Run the reviewer UI

```python
# reviewer_app.py
from xybench.streamlit import ReviewComponent

ReviewComponent(session_id="your-session-id")
```

```bash
streamlit run reviewer_app.py
```

### LangGraph integration

```python
from xybench.integrations.langgraph import create_review_node, route_after_review

review_node = create_review_node(
    content_key="draft",
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
```

## How it works

```
AI generates content
    ↓
SDK: await review(content)        ← developer writes this one line
    ↓
JSON stored locally + notification sent (Slack/email)
    ↓
Reviewer opens Streamlit UI, sees content
    ↓
Picks action (approve/reject/need_change/new_idea), writes reason
    ↓
Confirmation: "Feedback received, AI is regenerating"
    ↓
(if need_change) Agent regenerates with feedback
    ↓
Reviewer sees comparison view: original vs new version
    ↓
SDK returns result, agent continues
```

## Review actions

| Action | Description |
|--------|-------------|
| `approve` | Content is good, proceed |
| `reject` | Content is not acceptable, stop |
| `need_change` | Specific changes needed, triggers regeneration |
| `new_idea` | Reviewer suggests a different approach entirely |

## Storage

Reviews are stored as JSON files — one file per review, zero dependencies:

```
reviews/
    gen_abc123.json
    gen_def456.json
```

```json
{
  "output_id": "gen_abc123",
  "session_id": "thread-001",
  "content": "Original AI draft...",
  "new_content": "Regenerated draft...",
  "action": "need_change",
  "reason": "Section 3 formatting doesn't match requirements",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00Z",
  "reviewed_at": "2024-01-15T10:35:00Z"
}
```

## Configuration

All configuration is via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `XYBENCH_STORAGE_DIR` | Review storage directory | `./reviews` |
| `XYBENCH_SLACK_WEBHOOK_URL` | Slack incoming webhook URL | — |
| `XYBENCH_SMTP_HOST` | SMTP server host | `localhost` |
| `XYBENCH_SMTP_PORT` | SMTP server port | `587` |
| `XYBENCH_SMTP_USER` | SMTP username | — |
| `XYBENCH_SMTP_PASSWORD` | SMTP password | — |
| `XYBENCH_SMTP_FROM` | Email sender address | — |

## Development

```bash
# Setup dev environment
make dev

# Run tests
make test

# Lint & format
make lint
make format

# Run example
make example

# Run reviewer UI
make reviewer
```

## Roadmap

- **Now**: HITL eval (real-time, blocking, drives regeneration)
- **Next**: LLM judge eval (async, batch, automated)
- **Future**: Data flywheel (human reviews → train judges → reduce human involvement)

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
