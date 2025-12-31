# Durable Memory Example

This example demonstrates how to use CrewAI's memory system with Temporal's durable execution.

## What It Shows

- **Short-term memory**: Conversation context within a crew execution
- **Long-term memory**: Persistent learning across workflow executions
- **Entity memory**: Tracking entities (people, organizations, concepts)

All memory operations are routed through Temporal activities, making them:
- **Durable**: Survives worker crashes and restarts
- **Observable**: Visible in Temporal UI
- **Retryable**: Automatic retry on transient failures

## Running the Example

1. **Start Temporal server**:
   ```bash
   temporal server start-dev
   ```

2. **Start the worker**:
   ```bash
   uv run crewai_plugin/memory/run_worker.py
   ```

3. **Run the workflow**:
   ```bash
   uv run crewai_plugin/memory/run_memory_workflow.py
   ```

## Key Code Patterns

### Creating Memory Stubs

```python
from temporalio.contrib.crewai import (
    short_term_memory_stub,
    long_term_memory_stub,
    entity_memory_stub,
)

# Create durable storage stubs
stm_storage = short_term_memory_stub()
ltm_storage = long_term_memory_stub()
etm_storage = entity_memory_stub()
```

### Attaching Memory to Crew

```python
from crewai.memory.short_term.short_term_memory import ShortTermMemory
from crewai.memory.long_term.long_term_memory import LongTermMemory
from crewai.memory.entity.entity_memory import EntityMemory

crew = Crew(
    agents=[...],
    tasks=[...],
    memory=True,
    short_term_memory=ShortTermMemory(storage=stm_storage),
    long_term_memory=LongTermMemory(storage=ltm_storage),
    entity_memory=EntityMemory(storage=etm_storage),
)
```

### Worker Configuration

```python
from crewai.memory.storage.rag_storage import RAGStorage
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage

plugin = CrewAIPlugin(
    config=CrewAIActivityConfig(
        llm_factory=lambda model: LLM(model=model),
        # RAG storage for short-term and entity memory
        rag_storage_factory=lambda storage_type: RAGStorage(type=storage_type),
        # SQLite storage for long-term memory
        ltm_storage_factory=lambda db_path: LTMSQLiteStorage(db_path=db_path),
    )
)
```

## How It Works

1. **Workflow starts**: CrewAI crew is created with memory stubs
2. **Agent thinks**: LLM calls go through Temporal activities
3. **Memory saves**: Memory operations become Temporal activities
4. **Failure occurs**: Worker crashes mid-execution
5. **Recovery**: New worker picks up, memory state is preserved
6. **Continues**: Crew resumes with full memory context

## Benefits Over Standard CrewAI Memory

| Feature | Standard CrewAI | With Temporal |
|---------|-----------------|---------------|
| Crash recovery | Lost | Preserved |
| Observability | Limited | Full history |
| Retry on failure | Manual | Automatic |
| Cross-worker state | In-memory only | Persisted |
