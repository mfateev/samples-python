"""Worker for CrewAI tool configuration example.

This worker handles the tool config workflow and demonstrates
registering activities with different characteristics.
"""

import asyncio

from crewai import LLM
from temporalio.client import Client
from temporalio.contrib.crewai import CrewAIActivityConfig, CrewAIPlugin
from temporalio.envconfig import ClientConfig
from temporalio.worker import Worker

from crewai_plugin.tool_config.activities.tools import (
    flaky_external_api,
    gpu_intensive_task,
    quick_lookup,
    slow_analysis,
)
from crewai_plugin.tool_config.workflows.config_workflow import ToolConfigWorkflow


async def main():
    """Start the tool config workflow worker."""
    # Create plugin with LLM factory
    plugin = CrewAIPlugin(
        config=CrewAIActivityConfig(
            llm_factory=lambda model: LLM(model=model),
        )
    )

    # Load connection config from environment
    config = ClientConfig.load_client_connect_config()
    config.setdefault("target_host", "localhost:7233")

    # Connect to Temporal server
    client = await Client.connect(**config, plugins=[plugin])

    # Create main worker with most activities
    worker = Worker(
        client,
        task_queue="crewai-tools-task-queue",
        workflows=[ToolConfigWorkflow],
        activities=[
            quick_lookup,
            slow_analysis,
            flaky_external_api,
            # Note: gpu_intensive_task is NOT registered here
            # It should be handled by a specialized GPU worker
        ],
    )

    print("Starting CrewAI Tool Config worker...")
    print("Task queue: crewai-tools-task-queue")
    print("")
    print("Note: gpu_process tool is routed to 'gpu-workers' task queue.")
    print("For this demo, we also start a mock GPU worker.")
    print("Press Ctrl+C to stop")

    # For demo purposes, also start a mock "GPU worker"
    gpu_worker = Worker(
        client,
        task_queue="gpu-workers",
        activities=[gpu_intensive_task],
    )

    # Run both workers
    await asyncio.gather(
        worker.run(),
        gpu_worker.run(),
    )


if __name__ == "__main__":
    asyncio.run(main())
