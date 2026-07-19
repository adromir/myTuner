import logging
import asyncio
from typing import AsyncGenerator

class QueueHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.queues = []
        
    def emit(self, record):
        try:
            msg = self.format(record)
            # Create HTML snippet for SSE
            html = f"""
            <div class="font-mono text-sm border-b border-outline-variant/10 py-1 flex items-start gap-4">
                <span class="text-on-surface-variant/50 flex-shrink-0 w-40">{self.formatter.formatTime(record, "%Y-%m-%d %H:%M:%S")}</span>
                <span class="flex-shrink-0 w-16 font-bold {'text-error' if record.levelname == 'ERROR' else 'text-primary' if record.levelname == 'INFO' else 'text-tertiary'}">{record.levelname}</span>
                <span class="text-on-surface break-words">{msg}</span>
            </div>
            """
            for q in self.queues:
                try:
                    q.put_nowait(html)
                except asyncio.QueueFull:
                    pass
        except Exception:
            self.handleError(record)
            
    async def subscribe(self, request) -> AsyncGenerator[str, None]:
        q = asyncio.Queue(maxsize=100)
        self.queues.append(q)
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=2.0)
                    yield f"data: {msg}\n\n"
                except asyncio.TimeoutError:
                    # Keep-alive or just loop to check disconnect
                    pass
        finally:
            if q in self.queues:
                self.queues.remove(q)

queue_handler = QueueHandler()
formatter = logging.Formatter('%(message)s')
queue_handler.setFormatter(formatter)
queue_handler.setLevel(logging.INFO)

# Attach to root logger or mytuner logger
logging.getLogger("mytuner").addHandler(queue_handler)
