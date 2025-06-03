from typing import List

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from temporalio import activity

class InvokeModelInput(BaseModel):
    messages: List[BaseMessage]

@activity.defn
async def invoke_model(input: InvokeModelInput) -> BaseMessage:
# async def invoke_model(messages: List[BaseMessage]) -> BaseMessage:
    llm = ChatOpenAI()
    print("activity type of messages:", type(input.messages))
    print([type(x).__name__ for x in input.messages])

    return llm.invoke(input.messages)