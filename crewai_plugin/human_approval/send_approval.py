"""Send approval signal to a running workflow.

This script demonstrates sending signals to a workflow from
an external process - useful for integrating with external
approval systems, UIs, or APIs.
"""

import argparse
import asyncio

from temporalio.client import Client
from temporalio.contrib.crewai import CrewAIActivityConfig, CrewAIPlugin
from temporalio.envconfig import ClientConfig

from crewai_plugin.human_approval.workflows.approval_workflow import (
    ApprovalDecision,
    ContentApprovalWorkflow,
)


async def main():
    """Send approval or rejection to a workflow."""
    parser = argparse.ArgumentParser(description="Send approval to workflow")
    parser.add_argument(
        "--workflow-id",
        default="content-approval-workflow",
        help="Workflow ID to signal",
    )
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Approve the content",
    )
    parser.add_argument(
        "--reject",
        action="store_true",
        help="Reject and request revision",
    )
    parser.add_argument(
        "--feedback",
        default="",
        help="Feedback for rejection",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Just show current status",
    )

    args = parser.parse_args()

    # Create plugin for data conversion
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

    # Get workflow handle
    handle = client.get_workflow_handle(args.workflow_id)

    if args.status:
        # Just show status
        try:
            status = await handle.query(ContentApprovalWorkflow.get_status)
            print(f"Workflow: {args.workflow_id}")
            print(f"Revision count: {status['revision_count']}")
            print(f"Awaiting approval: {status['awaiting_approval']}")
            if status["proposal"]:
                print(f"\nCurrent proposal:\n{status['proposal'][:500]}...")
        except Exception as e:
            print(f"Error querying workflow: {e}")
        return

    if args.approve:
        await handle.signal(
            ContentApprovalWorkflow.submit_decision,
            ApprovalDecision(approved=True),
        )
        print(f"Approval sent to workflow {args.workflow_id}")

    elif args.reject:
        if not args.feedback:
            print("Error: --feedback is required when rejecting")
            return
        await handle.signal(
            ContentApprovalWorkflow.submit_decision,
            ApprovalDecision(approved=False, feedback=args.feedback),
        )
        print(f"Rejection sent to workflow {args.workflow_id}")
        print(f"Feedback: {args.feedback}")

    else:
        print("Please specify --approve, --reject, or --status")


if __name__ == "__main__":
    asyncio.run(main())
