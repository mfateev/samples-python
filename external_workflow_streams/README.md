# External Workflow Streams

> **Experimental.** This sample uses
> `temporalio.contrib.external_workflow_streams`. Its API may change in future
> versions.

This sample streams typed messages into a Workflow and streams processed
messages back to an external client. Payloads in both directions live in Redis
Streams instead of Temporal History. Temporal records compact metadata
describing which Redis offsets the Workflow consumed or published, so replay
uses the same immutable records and remains deterministic.

This is different from [`workflow_streams`](../workflow_streams), whose log is
hosted by the Workflow and whose events enter Temporal through Signals. External
Workflow Streams are intended for high-volume input and output where payload
size should not make History grow.

The sample has four parts:

- `workflow.py` subscribes to typed input with `external_stream` and publishes
  typed output with `external_output_stream`.
- `run_worker.py` configures the Worker with `RedisStreamBackend`.
- `run_publisher.py` binds an `ExternalStreamProducer` and an
  `ExternalOutputStreamClient` to the started Workflow chain. It appends an
  input batch without waking for every record, then concurrently prints the
  committed processed messages streamed back by the Workflow.
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

The publisher/client prints the Redis offset assigned to every input and output
record. The Worker logs each decoded input message, while the Workflow result
contains only the number of messages consumed. Set
`TEMPORAL_STREAMS_REDIS_URL` in both terminals to use a Redis instance other
than `redis://localhost:6379/0`.
