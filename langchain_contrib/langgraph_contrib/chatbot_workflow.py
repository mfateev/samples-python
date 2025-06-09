from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from langchain_contrib.langgraph_contrib.chatbot_activity import invoke_model, InvokeModelInput


@workflow.defn
class ChatbotWorkflow:
    def __init__(self) -> None:
        self._should_quit = False

    @workflow.run
    async def run(self) -> None:
        await workflow.wait_condition(lambda: self._should_quit)

    @workflow.update
    async def process_message(self, user_input: str) -> str:
        if user_input.lower() in ["quit", "q"]:
            self._should_quit = True
            return "Goodbye!"

        messages = [{"user", user_input}]

        # Invoke a model through an activity
        model_input = InvokeModelInput(messages=messages)
        response = await workflow.execute_activity(
            invoke_model,
            model_input,
            start_to_close_timeout=timedelta(seconds=60),
        )

        # Add assistant response to state
        messages.append(("assistant", response.content))

        return response.content
