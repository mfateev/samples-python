"""Tests for the Tool Configuration CrewAI workflow."""

import os
import uuid

import pytest
from crewai import LLM
from temporalio.client import Client
from temporalio.contrib.crewai import CrewAIActivityConfig, CrewAIPlugin
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import UnsandboxedWorkflowRunner, Worker

from crewai_plugin.tool_config.activities.tools import (
    flaky_external_api,
    gpu_intensive_task,
    quick_lookup,
    slow_analysis,
)
from crewai_plugin.tool_config.workflows.config_workflow import ToolConfigWorkflow


@pytest.fixture
def openai_api_key():
    """Ensure OpenAI API key is available."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        pytest.skip("OPENAI_API_KEY environment variable not set")
    return key


@pytest.fixture
def crewai_plugin(openai_api_key):
    """Create CrewAI plugin with OpenAI LLM factory."""
    return CrewAIPlugin(
        config=CrewAIActivityConfig(
            llm_factory=lambda model: LLM(model=model),
        )
    )


async def test_tool_config_workflow(crewai_plugin: CrewAIPlugin):
    """Test that the tool config workflow executes with different tool configurations."""
    task_queue = f"test-crewai-tools-{uuid.uuid4()}"
    gpu_task_queue = "gpu-workers"

    async with await WorkflowEnvironment.start_local() as env:
        # Create a new client with the plugin added
        new_config = env.client.config()
        existing_plugins = new_config.get("plugins", [])
        new_config["plugins"] = list(existing_plugins) + [crewai_plugin]
        plugin_client = Client(**new_config)

        # CrewAI workflows must run unsandboxed because Agent construction
        # calls open() to load prompt files.
        async with Worker(
            plugin_client,
            task_queue=task_queue,
            workflows=[ToolConfigWorkflow],
            activities=[
                quick_lookup,
                slow_analysis,
                flaky_external_api,
            ],
            workflow_runner=UnsandboxedWorkflowRunner(),
        ):
            # Start GPU worker for the gpu_intensive_task activity
            async with Worker(
                plugin_client,
                task_queue=gpu_task_queue,
                activities=[gpu_intensive_task],
            ):
                result = await plugin_client.execute_workflow(
                    ToolConfigWorkflow.run,
                    "renewable energy trends",
                    id=f"test-tool-config-{uuid.uuid4()}",
                    task_queue=task_queue,
                )

                # Verify we got a non-empty result
                assert result is not None
                assert len(result) > 0
