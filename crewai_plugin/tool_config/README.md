# Tool Configuration Example

This example demonstrates configuring `activity_as_tool()` with different options for various operational requirements.

## What It Shows

- **Custom timeouts**: Different timeout settings for fast vs slow operations
- **Retry policies**: Automatic retry with backoff for flaky operations
- **Heartbeat**: Progress tracking for long-running operations
- **Task queue routing**: Directing operations to specialized workers (e.g., GPU)

## Running the Example

1. **Start Temporal server**:
   ```bash
   temporal server start-dev
   ```

2. **Start the worker**:
   ```bash
   uv run crewai_plugin/tool_config/run_worker.py
   ```

3. **Run the workflow**:
   ```bash
   uv run crewai_plugin/tool_config/run_config_workflow.py
   ```

## Tool Configurations

### Quick Operations (Minimal Config)

```python
quick_tool = activity_as_tool(
    quick_lookup,
    name="quick_lookup",
    description="Fast database lookup",
)
```

Default 60-second timeout is sufficient for fast operations.

### Slow Operations (Extended Timeout + Heartbeat)

```python
slow_tool = activity_as_tool(
    slow_analysis,
    start_to_close_timeout=timedelta(minutes=10),
    heartbeat_timeout=timedelta(seconds=30),
    name="slow_analysis",
    description="Deep analysis that takes time",
)
```

- **Long timeout**: Allows operation to complete
- **Heartbeat**: Detects if worker dies mid-operation

### Flaky Operations (Retry Policy)

```python
flaky_tool = activity_as_tool(
    flaky_external_api,
    start_to_close_timeout=timedelta(seconds=30),
    retry_policy=RetryPolicy(
        initial_interval=timedelta(seconds=1),
        backoff_coefficient=2.0,
        maximum_interval=timedelta(seconds=30),
        maximum_attempts=5,
    ),
    name="external_api",
    description="External API (may need retries)",
)
```

- **Exponential backoff**: 1s → 2s → 4s → 8s → 16s
- **Max attempts**: 5 tries before failing

### Specialized Workers (Task Queue Routing)

```python
gpu_tool = activity_as_tool(
    gpu_intensive_task,
    task_queue="gpu-workers",  # Route to GPU pool
    start_to_close_timeout=timedelta(hours=1),
    heartbeat_timeout=timedelta(minutes=5),
    name="gpu_process",
    description="GPU-accelerated processing",
)
```

- **Custom task queue**: Only GPU workers pick up this work
- **Long timeout**: GPU operations may take hours

## Configuration Options Reference

| Option | Type | Description |
|--------|------|-------------|
| `start_to_close_timeout` | `timedelta` | Max time for single execution |
| `schedule_to_close_timeout` | `timedelta` | Total time including retries |
| `retry_policy` | `RetryPolicy` | Retry configuration |
| `heartbeat_timeout` | `timedelta` | Max time between heartbeats |
| `task_queue` | `str` | Route to specific workers |
| `cancellation_type` | `ActivityCancellationType` | How cancellation is handled |
| `name` | `str` | Override tool name |
| `description` | `str` | Override tool description |

## Worker Architecture

```
                    ┌─────────────────────────┐
                    │     Temporal Server     │
                    └───────────┬─────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
    │ Main Worker   │   │ GPU Worker    │   │ Other Workers │
    │ (default TQ)  │   │ (gpu-workers) │   │ (custom TQs)  │
    ├───────────────┤   ├───────────────┤   ├───────────────┤
    │ quick_lookup  │   │ gpu_task      │   │ ...           │
    │ slow_analysis │   └───────────────┘   └───────────────┘
    │ flaky_api     │
    └───────────────┘
```

## Observability

Open Temporal UI at http://localhost:8233 to see:
- Activity attempts and retries
- Heartbeat progress for slow operations
- Task queue routing
- Timeout and failure handling
