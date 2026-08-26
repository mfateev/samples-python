from __future__ import annotations

import asyncio
import uuid

from temporalio.client import Client
from temporalio.contrib.external_workflow_streams import (
    ExternalStreamProducer,
    WorkflowChainKey,
)

from external_workflow_streams.backend import create_backend
from external_workflow_streams.shared import (
    STREAM_NAME,
    TASK_QUEUE,
    StreamMessage,
)
from external_workflow_streams.workflow import MessageConsumerWorkflow

MESSAGES = [
    "payloads live in Redis",
    "History contains compact stream metadata",
    "the workflow still replays deterministically",
]


async def main() -> None:
    client = await Client.connect("localhost:7233")
    workflow_id = f"external-stream-{uuid.uuid4().hex[:8]}"
    handle = await client.start_workflow(
        MessageConsumerWorkflow.run,
        len(MESSAGES),
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    description = await handle.describe()
    chain = WorkflowChainKey(
        namespace=client.namespace,
        workflow_id=workflow_id,
        first_execution_run_id=(
            description.raw_description.workflow_execution_info.first_run_id
        ),
    )
    producer = await ExternalStreamProducer.connect(
        backend=create_backend(),
        workflow=chain,
        client=client,
        session_id=f"sample-publisher:{uuid.uuid4()}",
    )
    messages = producer.topic(STREAM_NAME, type=StreamMessage)

    for sequence, body in enumerate(MESSAGES, start=1):
        offset = await messages.publish(
            StreamMessage(sequence=sequence, body=body), wake=False
        )
        print(f"published message {sequence} at Redis offset {offset}")

    # One fence and wake announces the complete batch to the consumer.
    await messages.finish_writing()
    received = await handle.result()
    print(f"workflow consumed {received} messages")


if __name__ == "__main__":
    asyncio.run(main())
