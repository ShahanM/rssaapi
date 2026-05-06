import asyncio
import logging
from dataclasses import dataclass
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class BackgroundWriteCommand:
    task_name: str
    payload: dict[str, Any]


background_write_queue: asyncio.Queue[BackgroundWriteCommand] = asyncio.Queue(maxsize=1000)
