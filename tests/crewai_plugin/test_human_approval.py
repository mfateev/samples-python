"""Tests for the Human Approval CrewAI workflow."""

import asyncio
import os
import uuid

import pytest
from crewai import LLM
from temporalio.client import Client
from temporalio.contrib.crewai import CrewAIActivityConfig, CrewAIPlugin
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker, UnsandboxedWorkflowRunner

from crewai_plugin.human_approval.workflows.approval_workflow import (
    ApprovalDecision,
    ContentApprovalWorkflow,
)


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


async def test_approval_workflow_approved(crewai_plugin: CrewAIPlugin):
    """Test that the approval workflow completes when approved."""
    task_queue = f"test-crewai-approval-{uuid.uuid4()}"
    workflow_id = f"test-approval-{uuid.uuid4()}"

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
            workflows=[ContentApprovalWorkflow],
            workflow_runner=UnsandboxedWorkflowRunner(),
        ):
            # Start the workflow
            handle = await plugin_client.start_workflow(
                ContentApprovalWorkflow.run,
                "The Benefits of Exercise",
                id=workflow_id,
                task_queue=task_queue,
            )

            # Wait for proposal to be ready
            for _ in range(30):  # Max 60 seconds
                await asyncio.sleep(2)
                status = await handle.query(ContentApprovalWorkflow.get_status)
                if status["awaiting_approval"]:
                    break

            # Verify proposal was generated
            proposal = await handle.query(ContentApprovalWorkflow.get_proposal)
            assert proposal is not None
            assert len(proposal) > 0

            # Send approval signal
            await handle.signal(
                ContentApprovalWorkflow.submit_decision,
                ApprovalDecision(approved=True),
            )

            # Wait for workflow completion
            result = await handle.result()

            # Verify we got the final result
            assert result is not None
            assert "APPROVED" in result or len(result) > 0


async def test_approval_workflow_rejected_then_approved(crewai_plugin: CrewAIPlugin):
    """Test that the approval workflow handles rejection and revision."""
    task_queue = f"test-crewai-approval-{uuid.uuid4()}"
    workflow_id = f"test-approval-reject-{uuid.uuid4()}"

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
            workflows=[ContentApprovalWorkflow],
            workflow_runner=UnsandboxedWorkflowRunner(),
        ):
            # Start the workflow
            handle = await plugin_client.start_workflow(
                ContentApprovalWorkflow.run,
                "Remote Work Tips",
                id=workflow_id,
                task_queue=task_queue,
            )

            # Wait for first proposal
            for _ in range(30):
                await asyncio.sleep(2)
                status = await handle.query(ContentApprovalWorkflow.get_status)
                if status["awaiting_approval"]:
                    break

            # Reject with feedback
            await handle.signal(
                ContentApprovalWorkflow.submit_decision,
                ApprovalDecision(approved=False, feedback="Make it more concise"),
            )

            # Wait for revised proposal
            for _ in range(30):
                await asyncio.sleep(2)
                status = await handle.query(ContentApprovalWorkflow.get_status)
                if status["awaiting_approval"] and status["revision_count"] > 0:
                    break

            # Verify revision count increased
            status = await handle.query(ContentApprovalWorkflow.get_status)
            assert status["revision_count"] >= 1

            # Approve the revision
            await handle.signal(
                ContentApprovalWorkflow.submit_decision,
                ApprovalDecision(approved=True),
            )

            # Wait for completion
            result = await handle.result()
            assert result is not None
