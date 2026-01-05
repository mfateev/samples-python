"""Tests for the HelloWorld CrewAI workflow."""

import os
import uuid

import pytest
from crewai import LLM
from temporalio.client import Client
from temporalio.contrib.crewai import CrewAIActivityConfig, CrewAIPlugin
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker, UnsandboxedWorkflowRunner

from crewai_plugin.basic.workflows.hello_world_workflow import HelloWorldCrewWorkflow


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


async def test_hello_world_workflow(crewai_plugin: CrewAIPlugin):
    """Test that the hello world workflow generates a haiku."""
    task_queue = f"test-crewai-hello-{uuid.uuid4()}"

    # Start a local workflow environment
    async with await WorkflowEnvironment.start_local() as env:
        # Create a new client with the plugin added
        new_config = env.client.config()
        existing_plugins = new_config.get("plugins", [])
        new_config["plugins"] = list(existing_plugins) + [crewai_plugin]
        plugin_client = Client(**new_config)

        # CrewAI workflows must run unsandboxed because Agent construction
        # calls open() to load prompt files. The actual LLM calls run in
        # activities which are safe.
        async with Worker(
            plugin_client,
            task_queue=task_queue,
            workflows=[HelloWorldCrewWorkflow],
            workflow_runner=UnsandboxedWorkflowRunner(),
        ):
            result = await plugin_client.execute_workflow(
                HelloWorldCrewWorkflow.run,
                "autumn leaves",
                id=f"test-hello-world-{uuid.uuid4()}",
                task_queue=task_queue,
            )

            # Verify we got a non-empty result
            assert result is not None
            assert len(result) > 0
            # Haikus typically have multiple lines
            assert "\n" in result or len(result.split()) >= 10
