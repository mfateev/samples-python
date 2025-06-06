from __future__ import annotations

from temporalio import workflow
from temporalio.contrib.openai_agents.temporal_tools import activities_as_tools

with workflow.unsafe.imports_passed_through():
    from agents import Agent, Runner

    from openai_agents.workflows.get_weather_activity import get_weather


@workflow.defn
class ToolsWorkflow:
    @workflow.run
    async def run(self, question: str) -> str:
        agent = Agent(
            name="Hello world",
            instructions="You are a helpful agent.",
            # tools=[get_weather], # TODO: Discuss if tools should be list[Any].
            tools=activities_as_tools(get_weather),
            # tools=[activity_as_tool(get_weather)], # This is an alternative way to add an activity as a tool.
        )

        result = await Runner.run(agent, input=question)
        return result.final_output
