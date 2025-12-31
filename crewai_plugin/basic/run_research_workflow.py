"""Run the Research CrewAI workflow.

This script starts a multi-agent research workflow that investigates
a topic and produces a comprehensive report.
Make sure the worker is running before executing this script.
"""

import asyncio

from temporalio.client import Client
from temporalio.contrib.crewai import CrewAIActivityConfig, CrewAIPlugin

from crewai_plugin.basic.workflows.research_workflow import ResearchCrewWorkflow


async def main():
    """Execute the research workflow."""
    # Create plugin for proper data conversion
    plugin = CrewAIPlugin(
        config=CrewAIActivityConfig(
            llm_factory=lambda model: None,  # Not used on client side
        ),
        register_activities=False,  # Client doesn't need activities
    )

    # Connect to Temporal
    client = await Client.connect(
        "localhost:7233",
        plugins=[plugin],
    )

    # Execute workflow
    print("Starting Research CrewAI Workflow...")
    print("Topic: The Future of Renewable Energy")
    print("-" * 50)

    result = await client.execute_workflow(
        ResearchCrewWorkflow.run,
        "The Future of Renewable Energy",  # Research topic
        id="research-crew-workflow",
        task_queue="crewai-basic-task-queue",
    )

    print("\nResearch Report:")
    print("=" * 50)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
