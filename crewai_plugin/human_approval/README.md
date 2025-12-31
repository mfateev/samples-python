# Human Approval Example

This example demonstrates human-in-the-loop patterns using Temporal signals instead of CrewAI's `human_input=True` (which is not compatible with Temporal workflows).

## What It Shows

- **Workflow signals**: Receiving human decisions asynchronously
- **Workflow queries**: Checking workflow state (current proposal, status)
- **Revision loop**: Iterating based on human feedback
- **External integration**: Sending signals from separate processes

## Why Use Signals Instead of human_input?

CrewAI's `human_input=True` blocks the workflow waiting for console input, which doesn't work in distributed Temporal workflows. Signals provide a more powerful alternative:

| Feature | CrewAI human_input | Temporal Signals |
|---------|-------------------|------------------|
| Input source | Console only | Any (API, UI, mobile) |
| Wait duration | Limited | Unlimited (days/weeks) |
| Crash recovery | Lost | Preserved |
| External systems | Not possible | Full integration |

## Running the Example

1. **Start Temporal server**:
   ```bash
   temporal server start-dev
   ```

2. **Start the worker**:
   ```bash
   uv run crewai_plugin/human_approval/run_worker.py
   ```

3. **Run the interactive workflow**:
   ```bash
   uv run crewai_plugin/human_approval/run_approval_workflow.py
   ```

4. **Or send signals externally**:
   ```bash
   # Check status
   uv run crewai_plugin/human_approval/send_approval.py --status

   # Approve
   uv run crewai_plugin/human_approval/send_approval.py --approve

   # Request revision
   uv run crewai_plugin/human_approval/send_approval.py --reject --feedback "Add more examples"
   ```

## Key Code Patterns

### Defining Signals and Queries

```python
@workflow.defn
class ContentApprovalWorkflow:
    def __init__(self):
        self._proposal: str | None = None
        self._decision: ApprovalDecision | None = None

    @workflow.signal
    def submit_decision(self, decision: ApprovalDecision) -> None:
        """Receive human approval decision."""
        self._decision = decision

    @workflow.query
    def get_proposal(self) -> str | None:
        """Get current proposal for review."""
        return self._proposal
```

### Waiting for Human Input

```python
@workflow.run
async def run(self, topic: str) -> str:
    # Generate content with CrewAI
    self._proposal = await self._generate_content(topic)

    # Wait for human decision (can wait indefinitely)
    await workflow.wait_condition(lambda: self._decision is not None)

    if self._decision.approved:
        return self._proposal
    else:
        # Revise based on feedback
        return await self._revise_content(self._decision.feedback)
```

### Sending Signals from External Code

```python
# Get handle to running workflow
handle = client.get_workflow_handle("content-approval-workflow")

# Send approval signal
await handle.signal(
    ContentApprovalWorkflow.submit_decision,
    ApprovalDecision(approved=True),
)

# Or query current state
status = await handle.query(ContentApprovalWorkflow.get_status)
```

## Use Cases

- **Content moderation**: AI generates, humans approve before publishing
- **Code review**: AI writes code, developers approve changes
- **Financial approvals**: AI prepares reports, managers sign off
- **Legal review**: AI drafts contracts, lawyers verify compliance

## Workflow Lifecycle

```
[Start] → [Generate Content] → [Wait for Signal] → [Approved?]
                                      ↑                  ↓ No
                                      └──── [Revise] ←──┘
                                                         ↓ Yes
                                                   [Complete]
```
