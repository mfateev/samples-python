from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from openai_agents.adapters.temporal_openai_agents import TemporalModelProvider
    from agents import Agent, Runner, RunConfig, trace


@workflow.defn
class HelloWorldAgent:
    @workflow.run
    async def run(self, prompt: str) -> str:

        agent = Agent(
            name="Assistant",
            instructions="You only respond in haikus.",
        )
        config = RunConfig(model_provider=TemporalModelProvider())

        with trace("HellowWorld", group_id=workflow.info().workflow_id):
            result = await Runner.run(agent, input=prompt, run_config=config)
        return result.final_output
