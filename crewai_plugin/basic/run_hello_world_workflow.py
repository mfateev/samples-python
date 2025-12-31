"""Run the Hello World CrewAI workflow.

This script starts a workflow that creates a haiku about a given topic.
Make sure the worker is running before executing this script.
"""

import asyncio

from temporalio.client import Client
from temporalio.contrib.crewai import CrewAIActivityConfig, CrewAIPlugin
from temporalio.envconfig import ClientConfig

from crewai_plugin.basic.workflows.hello_world_workflow import HelloWorldCrewWorkflow


async def main():
    """Execute the hello world workflow."""
    # Create plugin for proper data conversion
    plugin = CrewAIPlugin(
        config=CrewAIActivityConfig(
            llm_factory=lambda model: None,  # Not used on client side
        ),
        register_activities=False,  # Client doesn't need activities
    )

    # Load connection config from environment
    config = ClientConfig.load_client_connect_config()
    config.setdefault("target_host", "localhost:7233")

    # Connect to Temporal
    client = await Client.connect(**config, plugins=[plugin])

    # Execute workflow
    print("Starting Hello World CrewAI Workflow...")
    print("-" * 40)

    result = await client.execute_workflow(
        HelloWorldCrewWorkflow.run,
        "artificial intelligence",  # Topic for the haiku
        id="hello-world-crew-workflow",
        task_queue="crewai-basic-task-queue",
    )

    print("\nResult:")
    print("-" * 40)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
