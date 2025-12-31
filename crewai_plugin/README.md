# Temporal CrewAI Integration Samples

These samples demonstrate how to use [CrewAI](https://github.com/crewAIInc/crewAI) with Temporal's durable execution engine.

See the [module documentation](https://github.com/temporalio/sdk-python/blob/main/temporalio/contrib/crewai/README.md) for detailed API reference.

## Overview

The integration combines:
- **Temporal workflows** for durable, crash-proof execution
- **CrewAI** for multi-agent AI crews with roles, goals, and collaboration

This approach ensures that AI agent workflows survive failures, automatically retry, and provide full observability.

## Prerequisites

- Temporal server [running locally](https://docs.temporal.io/cli/server#start-dev)
- Required dependencies installed via `uv sync`
- OpenAI API key set as environment variable: `export OPENAI_API_KEY=your_key_here`

## Examples

| Sample | Description |
|--------|-------------|
| [Basic Examples](./basic/README.md) | Hello world and multi-agent research crew |
| [Memory](./memory/README.md) | Durable memory (short-term, long-term, entity) |
| [Human Approval](./human_approval/README.md) | Human-in-the-loop via Temporal signals |
| [Tool Config](./tool_config/README.md) | Activity options: timeouts, retries, task queues |

## Quick Start

1. **Start Temporal server**:
   ```bash
   temporal server start-dev
   ```

2. **Set your OpenAI API key**:
   ```bash
   export OPENAI_API_KEY=your_key_here
   ```

3. **Start the worker**:
   ```bash
   uv run crewai_plugin/basic/run_worker.py
   ```

4. **Run a workflow** (in another terminal):
   ```bash
   uv run crewai_plugin/basic/run_hello_world_workflow.py
   ```

## Key Concepts

### LLM Stub

Use `llm_stub()` instead of `LLM()` in workflows:

```python
from temporalio.contrib.crewai import llm_stub

agent = Agent(
    role="Writer",
    llm=llm_stub("gpt-4"),  # Routes through Temporal activities
)
```

### Activity as Tool

Wrap Temporal activities as CrewAI tools:

```python
from temporalio.contrib.crewai import activity_as_tool

search_tool = activity_as_tool(
    search_web,
    start_to_close_timeout=timedelta(seconds=30),
)

agent = Agent(
    tools=[search_tool],
    llm=llm_stub("gpt-4"),
)
```

### Validated Execution

Use `TemporalCrewRunner` for validated crew execution:

```python
from temporalio.contrib.crewai import TemporalCrewRunner

crew = Crew(agents=[...], tasks=[...])
runner = TemporalCrewRunner(crew)  # Validates configuration
result = await runner.kickoff()
```

### Plugin Setup

Use `CrewAIPlugin` for simplified worker configuration:

```python
from temporalio.contrib.crewai import CrewAIPlugin, CrewAIActivityConfig

plugin = CrewAIPlugin(
    config=CrewAIActivityConfig(
        llm_factory=lambda model: LLM(model=model),
    )
)

client = await Client.connect("localhost:7233", plugins=[plugin])
```
