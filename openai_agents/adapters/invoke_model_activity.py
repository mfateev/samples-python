from dataclasses import dataclass
from typing import Union, Optional, List, Literal, Iterable, TypedDict, Any, cast

import httpx
from agents import OpenAIResponsesModel, TResponseInputItem, ModelSettings, Tool, AgentOutputSchemaBase, Handoff, \
    ModelTracing, ModelResponse, HandoffInputFilter, FunctionTool, FileSearchTool, WebSearchTool, ComputerTool, \
    RunContextWrapper, UserError, SpanError, ModelBehaviorError
from agents.util import _json, _error_tracing
from openai import AsyncOpenAI, NotGiven, NOT_GIVEN
from openai._types import Headers, Query, Body
from openai.types import ResponsesModel, Metadata, Reasoning
from openai.types.responses import ResponseInputParam, ResponseIncludable, ResponseTextConfigParam, \
    response_create_params, ToolParam, Response
from temporalio import activity

from custom_decorator.activity_utils import _auto_heartbeater


class OpenAIActivityInput(TypedDict, total=False):
    input: Union[str, ResponseInputParam]
    model: ResponsesModel
    include: Optional[List[ResponseIncludable]] | NotGiven = NOT_GIVEN
    instructions: Optional[str] | NotGiven = NOT_GIVEN
    max_output_tokens: Optional[int] | NotGiven = NOT_GIVEN
    metadata: Optional[Metadata] | NotGiven = NOT_GIVEN
    parallel_tool_calls: Optional[bool] | NotGiven = NOT_GIVEN
    previous_response_id: Optional[str] | NotGiven = NOT_GIVEN
    reasoning: Optional[Reasoning] | NotGiven = NOT_GIVEN
    service_tier: Optional[Literal["auto", "default", "flex"]] | NotGiven = NOT_GIVEN
    store: Optional[bool] | NotGiven = NOT_GIVEN
    stream: Optional[Literal[False]] | Literal[True] | NotGiven = NOT_GIVEN
    temperature: Optional[float] | NotGiven = NOT_GIVEN
    text: ResponseTextConfigParam | NotGiven = NOT_GIVEN
    tool_choice: response_create_params.ToolChoice | NotGiven = NOT_GIVEN
    tools: Iterable[ToolParam] | NotGiven = NOT_GIVEN
    top_p: Optional[float] | NotGiven = NOT_GIVEN
    truncation: Optional[Literal["auto", "disabled"]] | NotGiven = NOT_GIVEN
    user: str | NotGiven = NOT_GIVEN
    extra_headers: Headers | None = None
    extra_query: Query | None = None
    extra_body: Body | None = None
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN


@activity.defn
@_auto_heartbeater
async def invoke_open_ai_client(input: OpenAIActivityInput) -> Response:
    client = AsyncOpenAI()
    return await client.responses.create(**input)


@dataclass
class HandoffInput:
    tool_name: str
    tool_description: str
    input_json_schema: dict[str, Any]
    agent_name: str
    # input_filter: HandoffInputFilter | None = None
    strict_json_schema: bool = True


@dataclass
class FunctionToolInput:
    """A tool that wraps a function. In most cases, you should use  the `function_tool` helpers to
    create a FunctionTool, as they let you easily wrap a Python function.
    """

    name: str
    """The name of the tool, as shown to the LLM. Generally the name of the function."""

    description: str
    """A description of the tool, as shown to the LLM."""

    params_json_schema: dict[str, Any]
    """The JSON schema for the tool's parameters."""

    # on_invoke_tool: Callable[[RunContextWrapper[Any], str], Awaitable[Any]]
    """A function that invokes the tool with the given context and parameters. The params passed
    are:
    1. The tool run context.
    2. The arguments from the LLM, as a JSON string.

    You must return a string representation of the tool output, or something we can call `str()` on.
    In case of errors, you can either raise an Exception (which will cause the run to fail) or
    return a string error message (which will be sent back to the LLM).
    """

    strict_json_schema: bool = True
    """Whether the JSON schema is in strict mode. We **strongly** recommend setting this to True,
    as it increases the likelihood of correct JSON input."""


ToolInput = Union[FunctionToolInput, FileSearchTool, WebSearchTool]


@dataclass
class HandoffInput:
    tool_name: str
    tool_description: str
    input_json_schema: dict[str, Any]
    agent_name: str
    strict_json_schema: bool = True

_WRAPPER_DICT_KEY = "response"

@dataclass
class AgentOutputSchemaInput(AgentOutputSchemaBase):
    output_type_name: str | None
    is_wrapped: bool
    output_schema: dict[str, Any] | None
    strict_json_schema: bool

    def is_plain_text(self) -> bool:
        """Whether the output type is plain text (versus a JSON object)."""
        return self.output_type_name is None or self.output_type_name == 'str'

    def is_strict_json_schema(self) -> bool:
        """Whether the JSON schema is in strict mode."""
        return self.strict_json_schema

    def json_schema(self) -> dict[str, Any]:
        """The JSON schema of the output type."""
        if self.is_plain_text():
            raise UserError("Output type is plain text, so no JSON schema is available")
        return self.output_schema

    def validate_json(self, json_str: str) -> Any:
        raise NotImplementedError()

    def name(self) -> str:
        return self.output_type_name


class ActivityModelInput(TypedDict, total=False):
    model_name: str
    system_instructions: Optional[str]
    input: str | list[TResponseInputItem]
    model_settings: ModelSettings
    tools: list[ToolInput]
    output_schema: Optional[AgentOutputSchemaInput]
    handoffs: list[HandoffInput]
    tracing: ModelTracing
    previous_response_id: Optional[str]


@activity.defn
@_auto_heartbeater
async def invoke_open_ai_model(input: ActivityModelInput) -> ModelResponse:
    model = OpenAIResponsesModel(input['model_name'], AsyncOpenAI())

    async def empty_function(ctx: RunContextWrapper[Any], input: str) -> str:
        pass

    def make_tool(tool: ToolInput) -> Tool:
        match tool.name:
            case "file_search":
                return cast(FileSearchTool, tool)
            case "web_search_preview":
                return cast(WebSearchTool, tool)
            case "computer_search_preview":
                return cast(ComputerTool, tool)
            case _:
                return FunctionTool(name=tool.name,
                                    description=tool.description,
                                    params_json_schema=tool.params_json_schema,
                                    on_invoke_tool=empty_function,
                                    strict_json_schema=tool.strict_json_schema)

    tools = [make_tool(x) for x in input.get('tools', [])]
    handoffs = [Handoff(
        tool_name=x.tool_name,
        tool_description=x.tool_description,
        input_json_schema=x.input_json_schema,
        agent_name=x.agent_name,
        strict_json_schema=x.strict_json_schema
    ) for x in input.get('handoffs', [])]
    return await model.get_response(system_instructions=input.get('system_instructions'),
                                    input=input['input'],
                                    model_settings=input['model_settings'],
                                    tools=tools,
                                    output_schema=input.get('output_schema'),
                                    handoffs=handoffs,
                                    tracing=input['tracing'],
                                    previous_response_id=input.get('previous_response_id')
                                    )
