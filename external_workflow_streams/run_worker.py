from __future__ import annotations

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from external_workflow_streams.backend import create_backend
from external_workflow_streams.shared import TASK_QUEUE
from external_workflow_streams.workflow import MessageConsumerWorkflow


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[MessageConsumerWorkflow],
        external_stream_backend=create_backend(),
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
