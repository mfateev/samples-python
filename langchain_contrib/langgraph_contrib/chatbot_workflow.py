from typing import Annotated, List, Tuple
from typing_extensions import TypedDict
from temporalio import workflow
from datetime import timedelta

with workflow.unsafe.imports_passed_through():
    from langgraph.graph.message import add_messages
    from langchain_contrib.langgraph_contrib.chatbot_activity import invoke_model

class State(TypedDict):
    messages: Annotated[list, add_messages]

@workflow.defn
class ChatbotWorkflow:
    def __init__(self) -> None:
        self._state: State = {"messages": []}
        self._should_quit = False

    @workflow.run
    async def run(self) -> None:
        await workflow.wait_condition(lambda: self._should_quit)

    @workflow.update
    async def process_message(self, user_input: str) -> str:
        if user_input.lower() in ["quit", "q"]:
            self._should_quit = True
            return "Goodbye!"
            
        # Add user message to state
        self._state["messages"].append(("user", user_input))
        
        # Invoke a model through an activity
        response = await workflow.execute_activity(
            invoke_model,
            self._state["messages"],
            start_to_close_timeout=timedelta(seconds=60),
        )
        
        # Add assistant response to state
        self._state["messages"].append(("assistant", response.content))
        
        return response.content