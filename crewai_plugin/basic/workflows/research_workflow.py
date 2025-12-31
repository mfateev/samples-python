"""Research CrewAI Workflow.

This example demonstrates a multi-agent research crew with tools.
It shows how to:
- Use activity_as_tool() to wrap activities as CrewAI tools
- Create multiple collaborating agents
- Chain tasks with dependencies
"""

from datetime import timedelta

from crewai import Agent, Crew, Task
from temporalio import workflow
from temporalio.contrib.crewai import (
    TemporalCrewRunner,
    activity_as_tool,
    llm_stub,
)

from crewai_plugin.basic.activities.search_activity import search_web


@workflow.defn
class ResearchCrewWorkflow:
    """A research crew that investigates topics and produces reports.

    This workflow demonstrates:
    - Multiple agents with different roles
    - Using activity_as_tool() for external operations
    - Task dependencies and collaboration
    - TemporalCrewRunner validation
    """

    @workflow.run
    async def run(self, topic: str) -> str:
        """Run the research crew.

        Args:
            topic: The topic to research

        Returns:
            The final research report
        """
        # Create tools from activities
        # The search_web activity is wrapped as a CrewAI tool
        search_tool = activity_as_tool(
            search_web,
            start_to_close_timeout=timedelta(seconds=30),
            description="Search the web for information about any topic",
        )

        # Create the researcher agent
        researcher = Agent(
            role="Senior Research Analyst",
            goal=f"Conduct thorough research on {topic}",
            backstory="""You are an experienced research analyst with expertise
            in gathering and synthesizing information from multiple sources.
            You always verify facts and look for multiple perspectives.""",
            llm=llm_stub("gpt-4o-mini"),
            tools=[search_tool],
            verbose=True,
        )

        # Create the writer agent
        writer = Agent(
            role="Content Writer",
            goal="Transform research into clear, engaging content",
            backstory="""You are a skilled writer who excels at taking complex
            research and turning it into accessible, well-structured content.
            You focus on clarity, accuracy, and reader engagement.""",
            llm=llm_stub("gpt-4o-mini"),
            verbose=True,
        )

        # Create the research task
        research_task = Task(
            description=f"""Research the topic: {topic}

            Your research should:
            1. Use the search tool to find relevant information
            2. Gather facts from multiple sources
            3. Identify key themes and insights
            4. Note any controversies or different perspectives

            Provide a comprehensive research summary with your findings.""",
            expected_output="""A detailed research summary including:
            - Key facts and statistics
            - Main themes and insights
            - Different perspectives on the topic
            - Sources referenced""",
            agent=researcher,
        )

        # Create the writing task (depends on research)
        writing_task = Task(
            description=f"""Based on the research provided, write a comprehensive
            article about {topic}.

            The article should:
            1. Have a compelling introduction
            2. Present the main findings clearly
            3. Include relevant examples and evidence
            4. Conclude with key takeaways

            Target length: 500-700 words.""",
            expected_output="A well-structured article of 500-700 words",
            agent=writer,
        )

        # Create the crew with both agents and tasks
        crew = Crew(
            agents=[researcher, writer],
            tasks=[research_task, writing_task],
            verbose=True,
        )

        # Run with TemporalCrewRunner for validation
        runner = TemporalCrewRunner(crew)
        result = await runner.kickoff()

        return result.raw
