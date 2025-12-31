"""Human Approval CrewAI Workflow.

This example demonstrates human-in-the-loop patterns using Temporal signals.
Since CrewAI's human_input=True is not compatible with Temporal workflows,
we use Temporal's signal mechanism for human approvals instead.

This pattern is more powerful than CrewAI's built-in human input because:
- Approvals can come from external systems (APIs, UIs, mobile apps)
- The workflow can wait indefinitely without consuming resources
- Approval state is durable and survives failures
"""

from dataclasses import dataclass

from crewai import Agent, Crew, Task
from temporalio import workflow
from temporalio.contrib.crewai import TemporalCrewRunner, llm_stub


@dataclass
class ApprovalDecision:
    """Human approval decision."""

    approved: bool
    feedback: str = ""


@workflow.defn
class ContentApprovalWorkflow:
    """A workflow that generates content and waits for human approval.

    This demonstrates:
    - Running a CrewAI crew to generate content
    - Using Temporal signals for human approval
    - Revising content based on feedback
    - Workflow queries to check current state
    """

    def __init__(self) -> None:
        self._proposal: str | None = None
        self._decision: ApprovalDecision | None = None
        self._revision_count: int = 0
        self._max_revisions: int = 3

    @workflow.signal
    def submit_decision(self, decision: ApprovalDecision) -> None:
        """Signal handler for human approval decisions.

        This can be called from:
        - CLI tools
        - Web applications
        - Mobile apps
        - External APIs
        """
        self._decision = decision

    @workflow.query
    def get_proposal(self) -> str | None:
        """Query to get the current proposal awaiting approval."""
        return self._proposal

    @workflow.query
    def get_status(self) -> dict:
        """Query to get the current workflow status."""
        return {
            "proposal": self._proposal,
            "decision": (
                {
                    "approved": self._decision.approved,
                    "feedback": self._decision.feedback,
                }
                if self._decision
                else None
            ),
            "revision_count": self._revision_count,
            "awaiting_approval": self._proposal is not None and self._decision is None,
        }

    @workflow.run
    async def run(self, topic: str) -> str:
        """Run the content approval workflow.

        Args:
            topic: The topic to create content about

        Returns:
            The final approved content
        """
        while self._revision_count < self._max_revisions:
            # Generate or revise content
            if self._revision_count == 0:
                self._proposal = await self._generate_content(topic)
            else:
                self._proposal = await self._revise_content(
                    topic,
                    self._proposal or "",
                    self._decision.feedback if self._decision else "",
                )

            # Reset decision for new approval cycle
            self._decision = None

            # Wait for human decision via signal
            await workflow.wait_condition(lambda: self._decision is not None)

            if self._decision and self._decision.approved:
                return f"APPROVED CONTENT:\n\n{self._proposal}"

            self._revision_count += 1

        # Max revisions reached
        return f"MAX REVISIONS REACHED. Final content:\n\n{self._proposal}"

    async def _generate_content(self, topic: str) -> str:
        """Generate initial content using CrewAI."""
        writer = Agent(
            role="Content Writer",
            goal="Create compelling, accurate content",
            backstory="""You are an experienced content writer who creates
            engaging and informative content. You focus on clarity and
            accuracy while maintaining reader interest.""",
            llm=llm_stub("gpt-4o-mini"),
            verbose=True,
        )

        task = Task(
            description=f"""Write a short article about: {topic}

            Requirements:
            - 200-300 words
            - Clear and engaging
            - Factually accurate
            - Include a compelling headline""",
            expected_output="A well-written article with headline",
            agent=writer,
        )

        crew = Crew(agents=[writer], tasks=[task], verbose=True)
        runner = TemporalCrewRunner(crew)
        result = await runner.kickoff()
        return result.raw

    async def _revise_content(
        self, topic: str, current_content: str, feedback: str
    ) -> str:
        """Revise content based on human feedback."""
        editor = Agent(
            role="Content Editor",
            goal="Revise content based on feedback",
            backstory="""You are a skilled editor who improves content
            based on specific feedback. You preserve the original voice
            while addressing all concerns raised.""",
            llm=llm_stub("gpt-4o-mini"),
            verbose=True,
        )

        task = Task(
            description=f"""Revise the following content about {topic}
            based on the feedback provided.

            Current content:
            {current_content}

            Feedback to address:
            {feedback}

            Make targeted revisions to address the feedback while
            maintaining the overall quality and flow.""",
            expected_output="Revised content addressing all feedback",
            agent=editor,
        )

        crew = Crew(agents=[editor], tasks=[task], verbose=True)
        runner = TemporalCrewRunner(crew)
        result = await runner.kickoff()
        return result.raw
