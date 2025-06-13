from datetime import timedelta
from typing import Annotated, Dict, Any, Sequence, List

from langchain_core.messages import BaseMessage
from temporalio import workflow, common
from typing_extensions import TypedDict

with workflow.unsafe.imports_passed_through():
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.message import add_messages
    from langchain_contrib.langgraph_contrib.chatbot_activity import invoke_model, InvokeModelInput


class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


@workflow.defn(sandboxed=False)
class ChatbotGraphWorkflow:
    """Executes the chatbot Langgraph sample inside a Temporal workflow."""

    def __init__(self) -> None:
        self._state: State = {"messages": []}
        self._should_quit = False
        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        # Create graph
        graph = StateGraph(State)

        # Add chatbot node
        graph.add_node("chatbot", self._chatbot_node)

        # Add edges
        graph.add_edge(START, "chatbot")
        graph.add_edge("chatbot", END)

        return graph.compile()

    async def _chatbot_node(self, state: State) -> Dict[str, Any]:
        # Get response from activity
        messages = state["messages"]
        print("type of messages:", type(messages))
        print([type(x).__name__ for x in messages])

        response = await workflow.execute_activity(
            invoke_model,
            InvokeModelInput(messages=messages),
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=common.RetryPolicy(
                maximum_attempts=3,
            ),
        )

        # Return state update with new message
        return {"messages": response}

    @workflow.run
    async def run(self) -> None:
        await workflow.wait_condition(lambda: self._should_quit)

    @workflow.update
    async def process_message(self, user_input: str) -> str:
        if user_input.lower() in ["quit", "q"]:
            self._should_quit = True
            return "Goodbye!"

        # Process through graph
        result = await self._graph.ainvoke({'messages': ("user", user_input)})

        # Return the last message content
        return result["messages"][-1].content

    @workflow.query
    def get_messages(self) -> Sequence[BaseMessage]:
        """Query to get the current messages in the workflow."""
        return self._state["messages"]
