"""Memory CrewAI Workflow.

This example demonstrates durable memory in CrewAI crews using Temporal.
It shows how to:
- Use short_term_memory_stub() for conversation context
- Use long_term_memory_stub() for persistent learning
- Use entity_memory_stub() for entity tracking
"""

from crewai import Agent, Crew, Task
from crewai.memory.entity.entity_memory import EntityMemory
from crewai.memory.long_term.long_term_memory import LongTermMemory
from crewai.memory.short_term.short_term_memory import ShortTermMemory
from temporalio import workflow
from temporalio.contrib.crewai import (
    TemporalCrewRunner,
    entity_memory_stub,
    llm_stub,
    long_term_memory_stub,
    short_term_memory_stub,
)


@workflow.defn
class MemoryCrewWorkflow:
    """A crew that demonstrates durable memory capabilities.

    This workflow shows how memory persists across agent interactions
    and survives failures. The crew consists of:
    - A note-taker that remembers conversation context
    - An analyst that learns from past interactions
    """

    @workflow.run
    async def run(self, topic: str) -> str:
        """Run the memory-enabled crew.

        Args:
            topic: The topic to discuss and remember

        Returns:
            The final analysis with memory context
        """
        # Create durable memory storage stubs
        # These route memory operations through Temporal activities
        stm_storage = short_term_memory_stub()
        ltm_storage = long_term_memory_stub()
        etm_storage = entity_memory_stub()

        # Create the note-taker agent
        note_taker = Agent(
            role="Note Taker",
            goal="Record important information about the topic",
            backstory="""You are a meticulous note-taker who captures
            key details and context from conversations. You remember
            previous discussions and can reference them.""",
            llm=llm_stub("gpt-4o-mini"),
            verbose=True,
        )

        # Create the analyst agent
        analyst = Agent(
            role="Analyst",
            goal="Analyze topics using accumulated knowledge",
            backstory="""You are an analyst who builds on previous
            knowledge. You use past learnings to provide deeper
            insights over time.""",
            llm=llm_stub("gpt-4o-mini"),
            verbose=True,
        )

        # Create the note-taking task
        note_task = Task(
            description=f"""Take notes on the following topic: {topic}

            Your notes should:
            1. Capture key concepts and terminology
            2. Identify important entities (people, organizations, technologies)
            3. Note any relationships between entities
            4. Summarize the main points concisely""",
            expected_output="""Structured notes including:
            - Key concepts
            - Important entities
            - Relationships
            - Summary""",
            agent=note_taker,
        )

        # Create the analysis task
        analysis_task = Task(
            description=f"""Analyze the topic: {topic}

            Using the notes provided and any relevant past knowledge:
            1. Identify patterns and trends
            2. Draw connections to related topics
            3. Provide actionable insights
            4. Suggest areas for further exploration""",
            expected_output="""A comprehensive analysis with:
            - Key patterns identified
            - Connections to related topics
            - Actionable insights
            - Recommendations for further study""",
            agent=analyst,
        )

        # Create crew with all memory types enabled
        # Memory operations are routed through Temporal activities,
        # making them durable and recoverable after failures
        crew = Crew(
            agents=[note_taker, analyst],
            tasks=[note_task, analysis_task],
            memory=True,
            short_term_memory=ShortTermMemory(storage=stm_storage),
            long_term_memory=LongTermMemory(storage=ltm_storage),
            entity_memory=EntityMemory(storage=etm_storage),
            verbose=True,
        )

        # Run with TemporalCrewRunner for validation
        runner = TemporalCrewRunner(crew)
        result = await runner.kickoff()

        return result.raw
