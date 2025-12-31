"""Tool activities with different characteristics.

These activities demonstrate various scenarios that benefit from
different Temporal activity configurations:
- Quick operations (short timeout)
- Slow operations (long timeout, heartbeat)
- Flaky operations (retry policy)
- Specialized operations (custom task queue)
"""

import asyncio
import random

from temporalio import activity


@activity.defn
async def quick_lookup(key: str) -> str:
    """A fast database lookup operation.

    This operation is quick and reliable, so it needs minimal configuration.
    """
    # Simulate fast lookup
    await asyncio.sleep(0.1)
    return f"Value for '{key}': cached_result_123"


@activity.defn
async def slow_analysis(data: str) -> str:
    """A slow analysis operation that takes time.

    This operation is slow but reliable. It needs:
    - Longer timeout
    - Heartbeat to show progress
    """
    total_steps = 5
    for step in range(total_steps):
        # Report progress via heartbeat
        activity.heartbeat(f"Step {step + 1}/{total_steps}")
        await asyncio.sleep(1)  # Simulate work

    return f"Analysis complete for: {data[:50]}..."


@activity.defn
async def flaky_external_api(query: str) -> str:
    """An external API that sometimes fails.

    This operation is unreliable. It needs:
    - Retry policy with backoff
    - Multiple attempts
    """
    # Simulate flaky behavior (fails ~50% of first attempts)
    attempt = activity.info().attempt
    if attempt < 2 and random.random() < 0.5:
        raise RuntimeError(f"API temporarily unavailable (attempt {attempt})")

    await asyncio.sleep(0.5)
    return f"API response for: {query}"


@activity.defn
async def gpu_intensive_task(prompt: str) -> str:
    """A GPU-intensive operation.

    This operation should run on specialized GPU workers.
    It's configured with a custom task queue.
    """
    # In a real scenario, this would be picked up by GPU workers
    await asyncio.sleep(0.5)
    return f"GPU processed: {prompt}"
