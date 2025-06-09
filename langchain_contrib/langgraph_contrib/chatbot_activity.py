from typing import List, Annotated, Union, Any

from langchain_core.messages import BaseMessage, MessageLikeRepresentation, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from temporalio import activity

MessageModel = Annotated[
    Union[HumanMessage, AIMessage],  # not always safe; better to be explicit
    Field(discriminator="type")
]

MessageLikeRepresentationModel = Union[
    MessageModel, list[str], tuple[str, str], str, dict[str, Any]
]
class InvokeModelInput(BaseModel):
    messages: List[MessageLikeRepresentationModel]


@activity.defn
async def invoke_model(input: InvokeModelInput) -> BaseMessage:
    # async def invoke_model(messages: List[BaseMessage]) -> BaseMessage:
    llm = ChatOpenAI()
    print("activity type of messages:", type(input.messages))
    print([type(x).__name__ for x in input.messages])

    return llm.invoke(input.messages)
