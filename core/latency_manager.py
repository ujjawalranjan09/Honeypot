"""
Latency and Timing Manager for Honey-Pot
Handles simulated response delays and processing time tracking.
"""
import asyncio
import random
from typing import Tuple

class LatencyManager:
    def __init__(self):
        self.default_delay_range = (1.0, 3.0)

    async def sleep(self, delay_ms: int = None):
        """Simulate a delay in processing/typing."""
        if delay_ms is None:
            delay_sec = random.uniform(*self.default_delay_range)
        else:
            delay_sec = delay_ms / 1000.0

        await asyncio.sleep(delay_sec)
        return delay_sec

    def get_processing_time(self, start_time: float) -> float:
        """Calculate elapsed time in seconds."""
        import time
        return time.time() - start_time

latency_manager = LatencyManager()
