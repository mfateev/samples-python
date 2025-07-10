from __future__ import annotations

import asyncio
import concurrent.futures
from datetime import timedelta

from temporalio import workflow
from temporalio.client import Client
from temporalio.contrib.openai_agents.invoke_model_activity import ModelActivity
from temporalio.contrib.openai_agents.model_parameters import ModelActivityParameters
from temporalio.contrib.openai_agents.open_ai_data_converter import (
    open_ai_data_converter,
)
from temporalio.contrib.openai_agents.temporal_openai_agents import (
    set_open_ai_agent_temporal_overrides,
)
from temporalio.contrib.openai_agents.trace_interceptor import OpenAIAgentsTracingInterceptor
from temporalio.worker import Worker

from nexus_openai_agents.weather_service_handler import WeatherServiceHandler
from nexus_openai_agents.get_weather_workflow import GetWeatherWorkflow
from nexus_openai_agents.tools_workflow import ToolsAgentWorkflow


async def main():
    with set_open_ai_agent_temporal_overrides(
            model_params=ModelActivityParameters(start_to_close_timeout=timedelta(seconds=10)),
    ):
        # Create client connected to server at the given address
        client = await Client.connect(
            "localhost:7233",
            data_converter=open_ai_data_converter,
            interceptors=[OpenAIAgentsTracingInterceptor()],
        )

        model_activity = ModelActivity()
        worker = Worker(
            client,
            task_queue="weather-task-queue",
            workflows=[
                ToolsAgentWorkflow,
            ],
            activities=[
                model_activity.invoke_model_activity,
            ],
        )
        await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
