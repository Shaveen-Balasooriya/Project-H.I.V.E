import os
import json
import asyncio
import logging
from nats.aio.client import Client as NATS
from nats.js.api import StreamConfig, RetentionPolicy

logger = logging.getLogger("nats_jetstream_publisher")

class NATSJetstreamPublisher:
    def __init__(self):
        self.nc = None
        self.js = None
        self.initialized = False

        # Configurations (ENV overrides for easy portability)
        self.server_url = os.getenv("NATS_URL", "nats://hive-nats-server:4222")
        self.stream_name = os.getenv("NATS_STREAM", "honeypot")
        self.subject_name = os.getenv("NATS_SUBJECT", "honeypot.logs")


    async def connect(self):
        if self.initialized:
            return

        try:
            self.nc = NATS()
            await self.nc.connect(servers=[self.server_url])
            self.js = self.nc.jetstream()
            logger.info(f"Connected to NATS server at {self.server_url}")

            await self._ensure_stream()
            self.initialized = True
        except Exception as e:
            logger.error(f"Error connecting to NATS: {e}")
            raise

    async def _ensure_stream(self):
        try:
            await self.js.add_stream(
                config=StreamConfig(
                    name=self.stream_name,
                    subjects=[self.subject_name],
                    retention=RetentionPolicy.WORK_QUEUE,
                    storage="file",
                    max_age=3600,  # 1 hour retention (tweak if needed)
                )
            )
            logger.info(f"Stream '{self.stream_name}' with subject '{self.subject_name}' created.")
        except Exception as e:
            if "already in use" in str(e) or "stream name already in use" in str(e):
                logger.info(f"Stream '{self.stream_name}' already exists.")
            else:
                logger.error(f"Failed creating or verifying stream: {e}")
                raise

    async def publish(self, payload: dict):
        if not self.initialized:
            raise RuntimeError("Publisher not connected. Call connect() first.")

        try:
            message = json.dumps(payload).encode()
            await self.js.publish(self.subject_name, message)
            logger.info(f"Published log to {self.subject_name}: {payload.get('ip', 'unknown IP')}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    async def close(self):
        if self.nc:
            await self.nc.drain()
            await self.nc.close()
            self.initialized = False
            logger.info("NATS connection closed.")

# Example Usage (for testing inside container if needed)
if __name__ == "__main__":
    async def test():
        publisher = NATSJetstreamPublisher()
        await publisher.connect()
        await publisher.publish({"test": "hello from honeypot"})
        await publisher.close()

    asyncio.run(test())
