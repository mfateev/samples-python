# Basic CrewAI Examples

Simple examples to get started with CrewAI integrated with Temporal workflows.

## Prerequisites

Before running these examples:

1. **Start Temporal server**:
   ```bash
   temporal server start-dev
   ```

2. **Set your OpenAI API key**:
   ```bash
   export OPENAI_API_KEY=your_key_here
   ```

## Running the Examples

First, start the worker (supports all basic examples):

```bash
uv run crewai_plugin/basic/run_worker.py
```

Then run individual examples in separate terminals:

### Hello World Crew

A simple single-agent crew that writes haikus:

```bash
uv run crewai_plugin/basic/run_hello_world_workflow.py
```

This example demonstrates:
- Basic agent creation with `llm_stub()`
- Simple task definition
- `TemporalCrewRunner` validation

### Research Crew

A multi-agent research crew with tools:

```bash
uv run crewai_plugin/basic/run_research_workflow.py
```

This example demonstrates:
- Multiple collaborating agents (Researcher and Writer)
- Using `activity_as_tool()` for external operations
- Task chaining and dependencies
- Full crew validation

## Code Structure

```
basic/
├── activities/
│   └── search_activity.py    # Search tool as Temporal activity
├── workflows/
│   ├── hello_world_workflow.py   # Simple haiku writer
│   └── research_workflow.py      # Multi-agent research crew
├── run_worker.py                 # Worker for all examples
├── run_hello_world_workflow.py   # Execute hello world
└── run_research_workflow.py      # Execute research crew
```

## Key Patterns

### Agent with LLM Stub

```python
from temporalio.contrib.crewai import llm_stub

agent = Agent(
    role="Writer",
    goal="Write great content",
    backstory="You are an expert writer.",
    llm=llm_stub("gpt-4o-mini"),  # Use stub instead of LLM
)
```

### Activity as Tool

```python
from temporalio import activity
from temporalio.contrib.crewai import activity_as_tool

@activity.defn
async def search_web(query: str) -> str:
    # Your search implementation
    return "results..."

# In workflow:
search_tool = activity_as_tool(
    search_web,
    start_to_close_timeout=timedelta(seconds=30),
)

agent = Agent(
    tools=[search_tool],
    llm=llm_stub("gpt-4o-mini"),
)
```

### Validated Crew Execution

```python
from temporalio.contrib.crewai import TemporalCrewRunner

crew = Crew(agents=[...], tasks=[...])

# TemporalCrewRunner validates:
# - All agents use llm_stub()
# - All tools use activity_as_tool()
# - No human_input=True on tasks
# - No max_rpm rate limiting
runner = TemporalCrewRunner(crew)
result = await runner.kickoff()
```

## Observability

After running a workflow, open the Temporal UI at http://localhost:8233 to see:
- Workflow execution history
- Individual LLM call activities
- Tool execution activities
- Retry attempts and failures
- Workflow state and outputs
