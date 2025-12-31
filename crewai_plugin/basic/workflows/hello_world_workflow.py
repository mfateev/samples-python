"""Hello World CrewAI Workflow.

This is the simplest example of running a CrewAI crew in a Temporal workflow.
It demonstrates the basic pattern of using llm_stub() for LLM calls.
"""

from crewai import Agent, Crew, Task
from temporalio import workflow
from temporalio.contrib.crewai import TemporalCrewRunner, llm_stub


@workflow.defn
class HelloWorldCrewWorkflow:
    """A simple crew that writes haikus about any topic.

    This workflow demonstrates:
    - Creating an agent with llm_stub()
    - Creating a task for the agent
    - Running the crew with TemporalCrewRunner
    """

    @workflow.run
    async def run(self, topic: str) -> str:
        """Run the haiku writer crew.

        Args:
            topic: The topic to write a haiku about

        Returns:
            The generated haiku
        """
        # Create an agent using llm_stub() instead of direct LLM
        # The stub routes LLM calls through Temporal activities
        haiku_writer = Agent(
            role="Haiku Writer",
            goal="Write beautiful and meaningful haikus",
            backstory="""You are a master haiku poet with decades of experience.
            You follow the traditional 5-7-5 syllable structure and create
            haikus that capture the essence of any topic with elegance.""",
            llm=llm_stub("gpt-4o-mini"),
            verbose=True,
        )

        # Create a task for the agent
        write_haiku = Task(
            description=f"""Write a haiku about: {topic}

            Follow the traditional 5-7-5 syllable structure.
            The haiku should be thoughtful and capture the essence of the topic.
            Return only the haiku, nothing else.""",
            expected_output="A single haiku in 5-7-5 syllable format",
            agent=haiku_writer,
        )

        # Create the crew
        crew = Crew(
            agents=[haiku_writer],
            tasks=[write_haiku],
            verbose=True,
        )

        # Run with TemporalCrewRunner for validation
        runner = TemporalCrewRunner(crew)
        result = await runner.kickoff()

        return result.raw
