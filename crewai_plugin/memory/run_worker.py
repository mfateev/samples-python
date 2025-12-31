"""Worker for CrewAI memory example.

This worker handles the memory workflow which demonstrates
durable memory storage through Temporal activities.
"""

import asyncio

from crewai import LLM
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
from crewai.memory.storage.rag_storage import RAGStorage
from temporalio.client import Client
from temporalio.contrib.crewai import CrewAIActivityConfig, CrewAIPlugin
from temporalio.worker import Worker

from crewai_plugin.memory.workflows.memory_workflow import MemoryCrewWorkflow


async def main():
    """Start the memory workflow worker."""
    # Create plugin with LLM and memory storage factories
    plugin = CrewAIPlugin(
        config=CrewAIActivityConfig(
            # Factory to create LLM instances
            llm_factory=lambda model: LLM(model=model),
            # Factory for RAG-based memory (short-term, entity)
            rag_storage_factory=lambda storage_type: RAGStorage(type=storage_type),
            # Factory for SQLite-based memory (long-term)
            ltm_storage_factory=lambda db_path: LTMSQLiteStorage(db_path=db_path),
        )
    )

    # Connect to Temporal server
    client = await Client.connect(
        "localhost:7233",
        plugins=[plugin],
    )

    # Create worker
    worker = Worker(
        client,
        task_queue="crewai-memory-task-queue",
        workflows=[MemoryCrewWorkflow],
        # Note: Memory activities are automatically registered by the plugin
    )

    print("Starting CrewAI Memory worker...")
    print("Task queue: crewai-memory-task-queue")
    print("Press Ctrl+C to stop")

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
