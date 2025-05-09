from __future__ import annotations

from agents.items import TResponseStreamEvent
from temporalio import workflow

from openai_agents.adapters.invoke_model_activity import ToolInput, \
    FunctionToolInput, HandoffInput, AgentOutputSchemaInput

with workflow.unsafe.imports_passed_through():
    from datetime import timedelta
    from typing import Callable, Any, AsyncIterator, cast
    from agents.function_schema import function_schema
    from agents.models.openai_provider import DEFAULT_MODEL
    from openai_agents.adapters.invoke_model_activity import ActivityModelInput, invoke_open_ai_model
    from agents import ModelProvider, Model, Tool, RunContextWrapper, FunctionTool, \
        TResponseInputItem, ModelSettings, AgentOutputSchemaBase, Handoff, ModelTracing, ModelResponse, FileSearchTool, \
        WebSearchTool, AgentOutputSchema


def activity_as_tool(activity: Callable[..., Any]) -> Tool:
    async def run_activity(ctx: RunContextWrapper[Any], input: str) -> Any:
        return str(await workflow.execute_activity(
            activity,
            input,
            start_to_close_timeout=timedelta(seconds=10),
        ))

    schema = function_schema(activity)
    return FunctionTool(
        name=schema.name,
        description=schema.description or "",
        params_json_schema=schema.params_json_schema,
        on_invoke_tool=run_activity,
        strict_json_schema=True,
    )


class ActivityModelStubProvider(ModelProvider):
    def get_model(self, model_name: str | None) -> Model:
        if model_name is None:
            model_name = DEFAULT_MODEL
        return ActivityModel(model_name)


class ActivityModel(Model):
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    async def get_response(self, system_instructions: str | None, input: str | list[TResponseInputItem],
                           model_settings: ModelSettings, tools: list[Tool],
                           output_schema: AgentOutputSchemaBase | None, handoffs: list[Handoff], tracing: ModelTracing,
                           *, previous_response_id: str | None) -> ModelResponse:

        def make_tool_info(tool: Tool) -> ToolInput:
            match tool.name:
                case "file_search":
                    return cast(FileSearchTool, tool)
                case "web_search_preview":
                    return cast(WebSearchTool, tool)
                case "computer_search_preview":
                    raise NotImplementedError("Computer search preview is not supported in Temporal model")
                case _:
                    return FunctionToolInput(name=tool.name,
                                             description=tool.description,
                                             params_json_schema=tool.params_json_schema,
                                             strict_json_schema=tool.strict_json_schema)

        tool_infos = [make_tool_info(x) for x in tools] if tools is not None else None
        handoff_infos = [HandoffInput(
            tool_name=x.tool_name,
            tool_description=x.tool_description,
            input_json_schema=x.input_json_schema,
            agent_name=x.agent_name,
            strict_json_schema=x.strict_json_schema
        ) for x in handoffs] if handoffs is not None else None
        if output_schema is not None and not isinstance(output_schema, AgentOutputSchema):
            raise TypeError(
                f"Only AgentOutputSchema is supported by Temporal Model, got {type(output_schema).__name__}")
        agent_output_schema = cast(AgentOutputSchema, output_schema)
        output_schema_input = None if agent_output_schema is None else AgentOutputSchemaInput(
            output_type_name=agent_output_schema.name(),
            is_wrapped=agent_output_schema._is_wrapped,
            output_schema=agent_output_schema.json_schema() if not agent_output_schema.is_plain_text() else None,
            strict_json_schema=agent_output_schema.is_strict_json_schema(),
        )

        activity_input = ActivityModelInput(model_name=self.model_name,
                                            system_instructions=system_instructions,
                                            input=input,
                                            model_settings=model_settings,
                                            tools=tool_infos,
                                            output_schema=output_schema_input,
                                            handoffs=handoff_infos,
                                            tracing=tracing,
                                            previous_response_id=previous_response_id)
        return await workflow.execute_activity(
            invoke_open_ai_model,
            activity_input,
            start_to_close_timeout=timedelta(seconds=60),
            heartbeat_timeout=timedelta(seconds=10),
        )

    def stream_response(self, system_instructions: str | None, input: str | list[TResponseInputItem],
                        model_settings: ModelSettings, tools: list[Tool], output_schema: AgentOutputSchemaBase | None,
                        handoffs: list[Handoff], tracing: ModelTracing, *, previous_response_id: str | None) -> \
            AsyncIterator[TResponseStreamEvent]:
        raise NotImplementedError("Temporal model doesn't support streams yet")
