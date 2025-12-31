"""Run the Tool Configuration CrewAI workflow.

This script demonstrates a workflow where tools have different
activity configurations based on their operational characteristics.
"""

import asyncio

from temporalio.client import Client
from temporalio.contrib.crewai import CrewAIActivityConfig, CrewAIPlugin
from temporalio.envconfig import ClientConfig

from crewai_plugin.tool_config.workflows.config_workflow import ToolConfigWorkflow


async def main():
    """Execute the tool config workflow."""
    # Create plugin for proper data conversion
    plugin = CrewAIPlugin(
        config=CrewAIActivityConfig(
            llm_factory=lambda model: None,
        ),
        register_activities=False,
    )

    # Load connection config from environment
    config = ClientConfig.load_client_connect_config()
    config.setdefault("target_host", "localhost:7233")

    # Connect to Temporal
    client = await Client.connect(**config, plugins=[plugin])

    query = "Latest trends in renewable energy technology"

    print("Starting Tool Configuration Workflow...")
    print(f"Query: {query}")
    print("-" * 50)
    print("This workflow demonstrates tools with different configs:")
    print("  - quick_lookup: Fast, minimal config")
    print("  - slow_analysis: Long timeout + heartbeat")
    print("  - external_api: Retry policy for flaky API")
    print("  - gpu_process: Routed to GPU worker pool")
    print("-" * 50)

    result = await client.execute_workflow(
        ToolConfigWorkflow.run,
        query,
        id="tool-config-workflow",
        task_queue="crewai-tools-task-queue",
    )

    print("\nResult:")
    print("=" * 50)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
