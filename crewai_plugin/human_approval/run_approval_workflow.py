"""Run the Human Approval CrewAI workflow.

This script demonstrates the complete human-in-the-loop flow:
1. Starts a workflow that generates content
2. Queries the workflow for the proposal
3. Sends approval/rejection signals based on user input
"""

import asyncio

from temporalio.client import Client
from temporalio.contrib.crewai import CrewAIActivityConfig, CrewAIPlugin

from crewai_plugin.human_approval.workflows.approval_workflow import (
    ApprovalDecision,
    ContentApprovalWorkflow,
)


async def main():
    """Execute the approval workflow with interactive approval."""
    # Create plugin for proper data conversion
    plugin = CrewAIPlugin(
        config=CrewAIActivityConfig(
            llm_factory=lambda model: None,
        ),
        register_activities=False,
    )

    # Connect to Temporal
    client = await Client.connect(
        "localhost:7233",
        plugins=[plugin],
    )

    topic = "The Benefits of Remote Work"
    workflow_id = "content-approval-workflow"

    print("Starting Content Approval Workflow...")
    print(f"Topic: {topic}")
    print("-" * 50)

    # Start the workflow (don't wait for completion)
    handle = await client.start_workflow(
        ContentApprovalWorkflow.run,
        topic,
        id=workflow_id,
        task_queue="crewai-approval-task-queue",
    )

    print(f"Workflow started: {workflow_id}")
    print("Waiting for content generation...")

    # Poll for proposal to be ready
    while True:
        await asyncio.sleep(2)
        status = await handle.query(ContentApprovalWorkflow.get_status)
        if status["awaiting_approval"]:
            break
        print("  Still generating...")

    # Show the proposal
    proposal = await handle.query(ContentApprovalWorkflow.get_proposal)
    print("\n" + "=" * 50)
    print("PROPOSAL FOR REVIEW:")
    print("=" * 50)
    print(proposal)
    print("=" * 50)

    # Get user decision
    while True:
        print("\nOptions:")
        print("  [a] Approve")
        print("  [r] Request revision (provide feedback)")
        print("  [q] Quit (workflow continues running)")

        choice = input("\nYour choice: ").strip().lower()

        if choice == "a":
            # Send approval signal
            await handle.signal(
                ContentApprovalWorkflow.submit_decision,
                ApprovalDecision(approved=True),
            )
            print("\nApproval sent! Waiting for workflow to complete...")
            result = await handle.result()
            print("\n" + result)
            break

        elif choice == "r":
            feedback = input("Enter your feedback: ").strip()
            if feedback:
                await handle.signal(
                    ContentApprovalWorkflow.submit_decision,
                    ApprovalDecision(approved=False, feedback=feedback),
                )
                print("\nRevision requested. Waiting for new version...")

                # Wait for new proposal
                while True:
                    await asyncio.sleep(2)
                    status = await handle.query(ContentApprovalWorkflow.get_status)
                    if status["awaiting_approval"]:
                        break
                    print("  Revising...")

                # Show revised proposal
                proposal = await handle.query(ContentApprovalWorkflow.get_proposal)
                print("\n" + "=" * 50)
                print(f"REVISED PROPOSAL (revision #{status['revision_count']}):")
                print("=" * 50)
                print(proposal)
                print("=" * 50)
            else:
                print("Please provide feedback for revision.")

        elif choice == "q":
            print(f"\nWorkflow {workflow_id} continues running.")
            print("You can resume approval later using the send_approval.py script.")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    asyncio.run(main())
