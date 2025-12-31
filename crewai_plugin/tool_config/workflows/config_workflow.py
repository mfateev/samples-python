"""Tool Configuration CrewAI Workflow.

This example demonstrates configuring activity_as_tool() with
different options for various operational requirements:
- Custom timeouts for slow operations
- Retry policies for flaky operations
- Heartbeat for long-running operations
- Task queue routing for specialized workers
"""

from datetime import timedelta

from crewai import Agent, Crew, Task
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.contrib.crewai import TemporalCrewRunner, activity_as_tool, llm_stub

from crewai_plugin.tool_config.activities.tools import (
    flaky_external_api,
    gpu_intensive_task,
    quick_lookup,
    slow_analysis,
)


@workflow.defn
class ToolConfigWorkflow:
    """A workflow demonstrating different tool configurations.

    This shows how to configure activity_as_tool() for:
    - Quick operations (minimal config)
    - Slow operations (long timeout + heartbeat)
    - Flaky operations (retry policy)
    - Specialized operations (custom task queue)
    """

    @workflow.run
    async def run(self, query: str) -> str:
        """Run the tool configuration demo.

        Args:
            query: The query to process with various tools

        Returns:
            Combined results from all tools
        """
        # Tool 1: Quick lookup - minimal configuration
        # Default 60s timeout is fine for fast operations
        quick_tool = activity_as_tool(
            quick_lookup,
            name="quick_lookup",
            description="Fast database lookup for cached values",
        )

        # Tool 2: Slow analysis - extended timeout with heartbeat
        # Heartbeat lets us track progress and detect stuck activities
        slow_tool = activity_as_tool(
            slow_analysis,
            start_to_close_timeout=timedelta(minutes=10),
            heartbeat_timeout=timedelta(seconds=30),
            name="slow_analysis",
            description="Deep analysis that takes several minutes",
        )

        # Tool 3: Flaky API - aggressive retry policy
        # Retry with exponential backoff for transient failures
        flaky_tool = activity_as_tool(
            flaky_external_api,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                backoff_coefficient=2.0,
                maximum_interval=timedelta(seconds=30),
                maximum_attempts=5,
            ),
            name="external_api",
            description="Query external API (may need retries)",
        )

        # Tool 4: GPU task - route to specialized workers
        # This would go to workers with GPUs attached
        gpu_tool = activity_as_tool(
            gpu_intensive_task,
            task_queue="gpu-workers",  # Route to GPU worker pool
            start_to_close_timeout=timedelta(hours=1),
            heartbeat_timeout=timedelta(minutes=5),
            name="gpu_process",
            description="GPU-accelerated processing (runs on GPU workers)",
        )

        # Create agent with all tools
        researcher = Agent(
            role="Research Assistant",
            goal="Gather and analyze information using available tools",
            backstory="""You are a research assistant with access to various
            tools. You understand that different tools have different
            characteristics - some are fast, some are slow, some may
            fail and retry automatically.""",
            llm=llm_stub("gpt-4o-mini"),
            tools=[quick_tool, slow_tool, flaky_tool, gpu_tool],
            verbose=True,
        )

        # Create task that exercises multiple tools
        task = Task(
            description=f"""Research the following query: {query}

            Use the available tools appropriately:
            1. Use quick_lookup for fast cached data
            2. Use slow_analysis for deep analysis (this takes time)
            3. Use external_api for external data (may retry automatically)
            4. Use gpu_process only if heavy computation is needed

            Combine the results into a comprehensive response.""",
            expected_output="""A comprehensive response that includes:
            - Cached data from quick lookup
            - Deep analysis results
            - External API data
            - Summary and recommendations""",
            agent=researcher,
        )

        crew = Crew(agents=[researcher], tasks=[task], verbose=True)
        runner = TemporalCrewRunner(crew)
        result = await runner.kickoff()

        return result.raw
