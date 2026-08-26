# External Workflow Streams

> **Experimental.** This sample uses
> `temporalio.contrib.external_workflow_streams`. Its API may change in future
> versions.

This sample streams typed messages into a Workflow while keeping the message
payloads in Redis Streams instead of Temporal History. Temporal records compact
metadata describing which Redis offsets the Workflow consumed, so replay reads
the same immutable records and remains deterministic.

This is different from [`workflow_streams`](../workflow_streams), whose log is
hosted by the Workflow and whose events enter Temporal through Signals. External
Workflow Streams are intended for high-volume input where payload size should
not make History grow.

The sample has four parts:

- `workflow.py` subscribes to a typed external topic with `external_stream`.
- `run_worker.py` configures the Worker with `RedisStreamBackend`.
- `run_publisher.py` binds an `ExternalStreamProducer` to the started Workflow
  chain, appends a batch without waking for every record, then writes a fence
  and sends one wake.
- `backend.py` keeps the Redis URL and key prefix identical on both sides.

## Run it

Start a local Temporal server and Redis. For example:

```bash
temporal server start-dev
docker run --rm --name temporal-streams-redis -p 6379:6379 redis:7-alpine
```

Install the sample's Redis dependency:

```bash
uv sync --group external-workflow-streams
```

Start the Worker in one terminal:

```bash
uv run external_workflow_streams/run_worker.py
```

Run the publisher in another:

```bash
uv run external_workflow_streams/run_publisher.py
```

The publisher prints the Redis offset assigned to each record. The Worker logs
each decoded message, while the Workflow result contains only the number of
messages consumed. Set `TEMPORAL_STREAMS_REDIS_URL` in both terminals to use a
Redis instance other than `redis://localhost:6379/0`.
