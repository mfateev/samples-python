from dataclasses import replace

from agents import Runner, Agent, TContext, TResponseInputItem, RunHooks, RunConfig, RunResultStreaming, RunResult
from agents.run import DEFAULT_MAX_TURNS, DEFAULT_RUNNER, DefaultRunner
from requests.adapters import BaseAdapter
from temporalio import workflow
from temporalio.workflow import unsafe

from openai_agents.adapters.temporal_openai_agents import TemporalActivityModel


class TemporalOpenAIRunner(Runner):
    """
    Temporal Runner for OpenAI agents.
    TODO: Implement original runner forwarding
    """

    def __init__(self):
        self._runner = DEFAULT_RUNNER or DefaultRunner()

    async def _run_impl(self, starting_agent: Agent[TContext], input: str | list[TResponseInputItem], *,
                        context: TContext | None = None, max_turns: int = DEFAULT_MAX_TURNS,
                        hooks: RunHooks[TContext] | None = None, run_config: RunConfig | None = None,
                        previous_response_id: str | None = None) -> RunResult:
        if not workflow.in_workflow():
            return await self._runner._run_impl(
                starting_agent,
                input,
                context=context,
                max_turns=max_turns,
                hooks=hooks,
                run_config=run_config,
                previous_response_id=previous_response_id,
            )
        if run_config is None:
            run_config = RunConfig()

        if run_config.model is not None and not isinstance(run_config.model, str):
            raise ValueError("Temporal workflows require a model name to be a string in the run config.")
        updated_run_config = replace(run_config, model=TemporalActivityModel(run_config.model))
        return await self._runner._run_impl(starting_agent=starting_agent, input=input, context=context,
                                            max_turns=max_turns,
                                            hooks=hooks, run_config=updated_run_config,
                                            previous_response_id=previous_response_id)

    def _run_sync_impl(self, starting_agent: Agent[TContext], input: str | list[TResponseInputItem], *,
                       context: TContext | None = None, max_turns: int = DEFAULT_MAX_TURNS,
                       hooks: RunHooks[TContext] | None = None, run_config: RunConfig | None = None,
                       previous_response_id: str | None = None) -> RunResult:
        if not workflow.in_workflow():
            return self._runner._run_sync_impl(
                starting_agent,
                input,
                context=context,
                max_turns=max_turns,
                hooks=hooks,
                run_config=run_config,
                previous_response_id=previous_response_id,
            )
        raise RuntimeError("Temporal workflows do not support synchronous model calls.")

    def _run_streamed_impl(self, starting_agent: Agent[TContext], input: str | list[TResponseInputItem],
                           context: TContext | None = None, max_turns: int = DEFAULT_MAX_TURNS,
                           hooks: RunHooks[TContext] | None = None, run_config: RunConfig | None = None,
                           previous_response_id: str | None = None) -> RunResultStreaming:
        if not workflow.in_workflow():
            return self._runner._run_streamed_impl(
                starting_agent,
                input,
                context=context,
                max_turns=max_turns,
                hooks=hooks,
                run_config=run_config,
                previous_response_id=previous_response_id,
            )
        raise RuntimeError("Temporal workflows do not support streaming.")
