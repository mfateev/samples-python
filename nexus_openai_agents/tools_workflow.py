from __future__ import annotations

from datetime import timedelta

from temporalio import workflow

import nexus_openai_agents.get_weather_service_handler as weather_module
from nexus_openai_agents.get_weather_service import WeatherService

# Import our activity, passing it through the sandbox
with workflow.unsafe.imports_passed_through():
    from agents import Agent, Runner
    from temporalio.contrib.openai_agents.temporal_tools import nexus_operation_as_tool


@workflow.defn
class ToolsWorkflow:
    @workflow.run
    async def run(self, question: str) -> str:
        agent = Agent(
            name="Nexus Tool Example Agent",
            instructions="You are a helpful agent.",
            tools=[
                nexus_operation_as_tool(
                    WeatherService.get_weather,
                    service=WeatherService,
                    schedule_to_close_timeout=timedelta(hours=10),
                    endpoint="weather-service",
                )
            ],
        )

        result = await Runner.run(agent, input=question)
        return result.final_output


def process_order(order):
    ...
    prepare_shipment(order)
    ...


def prepare_shipment(order):
    ...

    charge_confirmation = charge(order.order_id, order.payment_info)
    shipment_confirmation = ship(order)
    send_email(order, charge_confirmation, shipment_confirmation)
