from __future__ import annotations as _annotations

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel
from temporalio import workflow

from pydantic_ai_temporal.adapters.temporal_model_provider import TemporalOpenAIProvider

with workflow.unsafe.imports_passed_through():
    from pydantic import BaseModel
    from temporalio import workflow


class MyModel(BaseModel):
    city: str
    country: str


@workflow.defn(sandboxed=False)
class PydanticModelWorkflow:

    @workflow.run
    async def run(self, prompt: str) -> str:
        model = OpenAIResponsesModel("gpt-3.5-turbo", provider=TemporalOpenAIProvider())
        agent = Agent(model, output_type=MyModel, instrument=True)
        result = await agent.run(prompt)
        return str(result.output)
