from __future__ import annotations

import asyncio
import uuid

from temporalio.client import Client
from temporalio.contrib.external_workflow_streams import (
    ExternalOutputStreamClient,
    ExternalStreamProducer,
    WorkflowChainKey,
)

from external_workflow_streams.backend import create_backend
from external_workflow_streams.shared import (
    INPUT_STREAM_NAME,
    OUTPUT_STREAM_NAME,
    TASK_QUEUE,
    ProcessedMessage,
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
    backend = create_backend()
    output_task: asyncio.Task[int] | None = None
    try:
        producer = await ExternalStreamProducer.connect(
            backend=backend,
            workflow=chain,
            client=client,
            session_id=f"sample-publisher:{uuid.uuid4()}",
        )
        messages = producer.topic(INPUT_STREAM_NAME, type=StreamMessage)
        output_client = await ExternalOutputStreamClient.connect(
            backend=backend,
            workflow=chain,
            client=client,
        )
        processed_messages = output_client.topic(
            OUTPUT_STREAM_NAME, type=ProcessedMessage
        )

        async def receive_processed_messages() -> int:
            received = 0
            async for item in processed_messages.subscribe():
                print(
                    "client received processed message "
                    f"{item.data.sequence} at Redis offset {item.offset}: "
                    f"{item.data.body}"
                )
                received += 1
            return received

        # Subscribe before publishing input so output can be observed as soon as
        # each producing Workflow Task commits its compact History marker.
        output_task = asyncio.create_task(receive_processed_messages())
        for sequence, body in enumerate(MESSAGES, start=1):
            offset = await messages.publish(
                StreamMessage(sequence=sequence, body=body), wake=False
            )
            print(f"published message {sequence} at Redis offset {offset}")

        # One fence and wake announces the complete input batch to the Workflow.
        await messages.finish_writing()
        workflow_received = await handle.result()
        client_received = await output_task
        if client_received != workflow_received:
            raise RuntimeError(
                "the output stream ended before every input had a processed result"
            )
        print(
            f"workflow consumed {workflow_received} messages and streamed "
            f"{client_received} processed messages to the client"
        )
    finally:
        if output_task is not None and not output_task.done():
            output_task.cancel()
            try:
                await output_task
            except asyncio.CancelledError:
                pass
        await backend.aclose()


if __name__ == "__main__":
    asyncio.run(main())
