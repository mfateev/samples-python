from dataclasses import dataclass
from typing import Union, Optional, List, Literal, Iterable, TypedDict, Any, cast

import httpx
from agents import OpenAIResponsesModel, TResponseInputItem, ModelSettings, Tool, AgentOutputSchemaBase, Handoff, \
    ModelTracing, ModelResponse, HandoffInputFilter, FunctionTool, FileSearchTool, WebSearchTool, ComputerTool, \
    RunContextWrapper
from openai import AsyncOpenAI, NotGiven, NOT_GIVEN, BaseModel
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
    """A handoff is when an agent delegates a task to another agent.
    For example, in a customer support scenario you might have a "triage agent" that determines
    which agent should handle the user's request, and sub-agents that specialize in different
    areas like billing, account management, etc.
    """

    tool_name: str
    """The name of the tool that represents the handoff."""

    tool_description: str
    """The description of the tool that represents the handoff."""

    input_json_schema: dict[str, Any]
    """The JSON schema for the handoff input. Can be empty if the handoff does not take an input.
    """

    # on_invoke_handoff: Callable[[RunContextWrapper[Any], str], Awaitable[Agent[TContext]]]
    """The function that invokes the handoff. The parameters passed are:
    1. The handoff run context
    2. The arguments from the LLM, as a JSON string. Empty string if input_json_schema is empty.

    Must return an agent.
    """

    agent_name: str
    """The name of the agent that is being handed off to."""

    input_filter: HandoffInputFilter | None = None
    """A function that filters the inputs that are passed to the next agent. By default, the new
    agent sees the entire conversation history. In some cases, you may want to filter inputs e.g.
    to remove older inputs, or remove tools from existing inputs.

    The function will receive the entire conversation history so far, including the input item
    that triggered the handoff and a tool call output item representing the handoff tool's output.

    You are free to modify the input history or new items as you see fit. The next agent that
    runs will receive `handoff_input_data.all_items`.

    IMPORTANT: in streaming mode, we will not stream anything as a result of this function. The
    items generated before will already have been streamed.
    """

    strict_json_schema: bool = True
    """Whether the input JSON schema is in strict mode. We **strongly** recommend setting this to
    True, as it increases the likelihood of correct JSON input.
    """


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

class ActivityModelInput(TypedDict, total=False):
    # model_config = {
    #     "arbitrary_types_allowed": True,
    # }

    model_name: str
    system_instructions: Optional[str]
    input: str | list[TResponseInputItem]
    model_settings: ModelSettings
    tools: list[ToolInput]
    output_schema: Optional[AgentOutputSchemaBase]
    # handoffs: list[Handoff]
    tracing: ModelTracing
    previous_response_id: Optional[str]


@activity.defn
@_auto_heartbeater
async def invoke_open_ai_model(input: ActivityModelInput) -> ModelResponse:
    client = OpenAIResponsesModel(input['model_name'], AsyncOpenAI())

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
    return await client.get_response(system_instructions=input.get('system_instructions'),
                                     input=input['input'],
                                     model_settings=input['model_settings'],
                                     tools=tools,
                                     output_schema=input.get('output_schema'),
                                     handoffs=[],
                                     tracing=input['tracing'],
                                     previous_response_id=input.get('previous_response_id')
                                     )
