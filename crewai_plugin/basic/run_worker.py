"""Worker for CrewAI basic examples.

This worker handles both the hello world and research workflows.
Run this before executing any workflow.
"""

import asyncio
import dataclasses

from crewai import LLM
from temporalio.client import Client
from temporalio.contrib.crewai import CrewAIActivityConfig, CrewAIPlugin
from temporalio.envconfig import ClientConfig
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner, SandboxRestrictions

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

    # Load connection config from environment
    config = ClientConfig.load_client_connect_config()
    config.setdefault("target_host", "localhost:7233")

    # Connect to Temporal server with the plugin
    client = await Client.connect(**config, plugins=[plugin])

    # Configure sandbox to allow open() for CrewAI's prompt file loading.
    # CrewAI's Agent initialization reads prompt files via I18N.load_prompts().
    # We unrestrict __builtins__.open and pass through crewai modules so the
    # @lru_cache on get_i18n() shares state with pre-warmed cache.
    restrictions = dataclasses.replace(
        SandboxRestrictions.default,
        invalid_module_members=SandboxRestrictions.invalid_module_members_default.with_child_unrestricted(
            "__builtins__", "open"
        ),
    ).with_passthrough_modules("crewai")

    workflow_runner = SandboxedWorkflowRunner(restrictions=restrictions)

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
        workflow_runner=workflow_runner,
    )

    print("Starting CrewAI worker...")
    print("Task queue: crewai-basic-task-queue")
    print("Press Ctrl+C to stop")

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
