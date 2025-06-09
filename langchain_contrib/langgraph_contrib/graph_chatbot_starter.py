import asyncio

from temporalio import common
from temporalio.client import Client, WithStartWorkflowOperation
from temporalio.contrib.pydantic import pydantic_data_converter

from langchain_contrib.langgraph_contrib.chatbot_graph_workflow import ChatbotGraphWorkflow


async def handle_message(
    message: str, temporal_client: Client
) -> str:
    """
    Handle a client message using update-with-start pattern.
    Creates a new workflow if it doesn't exist, or updates existing one.
    """
    start_op = WithStartWorkflowOperation(
        ChatbotGraphWorkflow.run,
        id="chatbot-graph-workflow",
        id_conflict_policy=common.WorkflowIDConflictPolicy.USE_EXISTING,
        task_queue="chatbot-task-queue",
    )
    
    try:
        response = await temporal_client.execute_update_with_start_workflow(
            ChatbotGraphWorkflow.process_message,
            message,
            start_workflow_operation=start_op,
        )
        return response
    except Exception as e:
        print(f"Error processing message: {e}")
        return "Sorry, there was an error processing your message."

async def main():
    client = await Client.connect("localhost:7233", data_converter=pydantic_data_converter)
    
    print("Chatbot started! Type 'quit' or 'q' to exit.")
    while True:
        user_input = input("User: ")
        
        response = await handle_message(user_input, client)
        print("Assistant:", response)
        
        if user_input.lower() in ["quit", "q"]:
            break

if __name__ == "__main__":
    asyncio.run(main()) 