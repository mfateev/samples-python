"""Worker for CrewAI basic examples.

This worker handles both the hello world and research workflows.
Run this before executing any workflow.
"""

import asyncio

from crewai import LLM
from temporalio.client import Client
from temporalio.contrib.crewai import CrewAIActivityConfig, CrewAIPlugin
from temporalio.worker import Worker

from crewai_plugin.basic.activities.search_activity import search_web
from crewai_plugin.basic.workflows.hello_world_workflow import HelloWorldCrewWorkflow
from crewai_plugin.basic.workflows.research_workflow import ResearchCrewWorkflow


async def main():
    """Start the CrewAI worker."""
    # Create plugin with LLM factory
    # The factory creates LLM instances for the activity side
    plugin = CrewAIPlugin(
        config=CrewAIActivityConfig(
            llm_factory=lambda model: LLM(model=model),
        )
    )

    # Connect to Temporal server with the plugin
    client = await Client.connect(
        "localhost:7233",
        plugins=[plugin],
    )

    # Create worker with workflows and custom activities
    # Note: CrewAI activities (llm_call, memory, etc.) are registered by the plugin
    worker = Worker(
        client,
        task_queue="crewai-basic-task-queue",
        workflows=[
            HelloWorldCrewWorkflow,
            ResearchCrewWorkflow,
        ],
        activities=[
            search_web,  # Custom activity for the research workflow
        ],
    )

    print("Starting CrewAI worker...")
    print("Task queue: crewai-basic-task-queue")
    print("Press Ctrl+C to stop")

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
