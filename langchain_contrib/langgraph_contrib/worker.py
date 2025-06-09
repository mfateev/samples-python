import asyncio

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from langchain_contrib.langgraph_contrib.chatbot_activity import invoke_model
from langchain_contrib.langgraph_contrib.chatbot_graph_workflow import ChatbotGraphWorkflow
from langchain_contrib.langgraph_contrib.chatbot_workflow import ChatbotWorkflow


async def main():
    client = await Client.connect("localhost:7233", data_converter=pydantic_data_converter)
    
    worker = Worker(
        client,
        task_queue="chatbot-task-queue",
        workflows=[ChatbotWorkflow, ChatbotGraphWorkflow],
        activities=[invoke_model],
    )
    
    await worker.run() 

interrupt_event = asyncio.Event()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nInterrupt received, shutting down...\n")
        interrupt_event.set()
        loop.run_until_complete(loop.shutdown_asyncgens())
