import asyncio
import uuid

from temporalio import worker
from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from pydanticai.invoke_pydantic_model_activity import invoke_pydantic_model_activity
from pydanticai.pydantic_model_workflow import PydanticModelWorkflow

TASK_QUEUE = "pydantic-model-task-queue"


async def main():
    # Uncomment the lines below to see logging output
    # import logging
    # logging.basicConfig(level=logging.INFO)

    # Start client
    client = await Client.connect("localhost:7233", data_converter=pydantic_data_converter)
    # client = await Client.connect("localhost:7233", data_converter=agents_data_converter)

    # Run a worker for the workflow
    async with Worker(
            client,
            task_queue=TASK_QUEUE,
            workflows=[PydanticModelWorkflow],
            activities=[invoke_pydantic_model_activity],
            unsandboxed_workflow_runner=worker.UnsandboxedWorkflowRunner()
    ):
        # While the worker is running, use the client to run the workflow and
        # print out its result. Note, in many production setups, the client
        # would be in a completely separate process from the worker.
        result = await client.execute_workflow(
            PydanticModelWorkflow.run,
            'The windy city in the US of A.',
            id="pydantic-model-workflow-id",
            task_queue=TASK_QUEUE,
            id_reuse_policy=WorkflowIDReusePolicy.TERMINATE_IF_RUNNING,
        )
        print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
