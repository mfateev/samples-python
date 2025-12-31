"""Worker for CrewAI human approval example.

This worker handles the approval workflow which demonstrates
human-in-the-loop patterns using Temporal signals.
"""

import asyncio

from crewai import LLM
from temporalio.client import Client
from temporalio.contrib.crewai import CrewAIActivityConfig, CrewAIPlugin
from temporalio.worker import Worker

from crewai_plugin.human_approval.workflows.approval_workflow import (
    ContentApprovalWorkflow,
)


async def main():
    """Start the approval workflow worker."""
    # Create plugin with LLM factory
    plugin = CrewAIPlugin(
        config=CrewAIActivityConfig(
            llm_factory=lambda model: LLM(model=model),
        )
    )

    # Connect to Temporal server
    client = await Client.connect(
        "localhost:7233",
        plugins=[plugin],
    )

    # Create worker
    worker = Worker(
        client,
        task_queue="crewai-approval-task-queue",
        workflows=[ContentApprovalWorkflow],
    )

    print("Starting CrewAI Approval worker...")
    print("Task queue: crewai-approval-task-queue")
    print("Press Ctrl+C to stop")

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
