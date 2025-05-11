from __future__ import annotations as _annotations

from temporalio import workflow

from pydanticai.pydantic_temporal_model import TemporalPydanticModel

with workflow.unsafe.imports_passed_through():
    from pydantic import BaseModel
    from temporalio import workflow
    from pydantic_ai import Agent


class MyModel(BaseModel):
    city: str
    country: str


@workflow.defn(sandboxed=False)
class PydanticModelWorkflow:

    @workflow.run
    async def run(self, prompt: str) -> str:
        model = TemporalPydanticModel(model_name="gpt-3.5-turbo")
        agent = Agent(model, output_type=MyModel, instrument=True)
        result = await agent.run(prompt)
        return str(result.output)
