"""Run the Memory CrewAI workflow.

This script starts a workflow that demonstrates durable memory
with CrewAI crews. Run multiple times to see memory accumulation.
"""

import asyncio

from temporalio.client import Client
from temporalio.contrib.crewai import CrewAIActivityConfig, CrewAIPlugin
from temporalio.envconfig import ClientConfig

from crewai_plugin.memory.workflows.memory_workflow import MemoryCrewWorkflow


async def main():
    """Execute the memory workflow."""
    # Create plugin for proper data conversion
    plugin = CrewAIPlugin(
        config=CrewAIActivityConfig(
            llm_factory=lambda model: None,  # Not used on client side
        ),
        register_activities=False,
    )

    # Load connection config from environment
    config = ClientConfig.load_client_connect_config()
    config.setdefault("target_host", "localhost:7233")

    # Connect to Temporal
    client = await Client.connect(**config, plugins=[plugin])

    # Execute workflow
    topic = "Machine Learning in Healthcare"
    print("Starting Memory CrewAI Workflow...")
    print(f"Topic: {topic}")
    print("-" * 50)
    print("This crew uses durable memory that persists across:")
    print("- Agent interactions (short-term)")
    print("- Workflow executions (long-term)")
    print("- Entity tracking (entity memory)")
    print("-" * 50)

    result = await client.execute_workflow(
        MemoryCrewWorkflow.run,
        topic,
        id="memory-crew-workflow",
        task_queue="crewai-memory-task-queue",
    )

    print("\nAnalysis Result:")
    print("=" * 50)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
