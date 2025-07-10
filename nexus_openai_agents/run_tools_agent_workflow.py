import asyncio
import uuid
from datetime import timedelta

from temporalio.client import Client
from temporalio.contrib.openai_agents.model_parameters import ModelActivityParameters
from temporalio.contrib.openai_agents.open_ai_data_converter import (
    open_ai_data_converter,
)
from temporalio.contrib.openai_agents.temporal_openai_agents import set_open_ai_agent_temporal_overrides
from temporalio.contrib.openai_agents.trace_interceptor import OpenAIAgentsTracingInterceptor

from nexus_openai_agents.tools_workflow import ToolsAgentWorkflow


# noinspection PyTypeChecker
async def main():
    # Create client connected to server at the given address
    with set_open_ai_agent_temporal_overrides(
            model_params=ModelActivityParameters(start_to_close_timeout=timedelta(seconds=10)),
    ):
        client = await Client.connect(
            "localhost:7233",
            data_converter=open_ai_data_converter,
            interceptors=[OpenAIAgentsTracingInterceptor()],
        )

        # Execute a workflow
        result = await client.execute_workflow(
            ToolsAgentWorkflow.run,
            "What is the weather in Berlin?",
            id=f"tools-workflow-{uuid.uuid4()}",
            task_queue="weather-task-queue",
        )

    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
