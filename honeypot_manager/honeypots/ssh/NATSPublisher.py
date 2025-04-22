import json
import logging  # Import logging
from nats.aio.client import Client as NATS
from typing import Optional
import os

# Get a logger instance
logger = logging.getLogger(__name__)

class NATSPublisher:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(NATSPublisher, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.nc: Optional[NATS] = None
        self.js = None
        self.initialized = False

    async def initialize(self, server_url=None):
        if self.initialized:
            return
        try:
            server_url = server_url or os.getenv("NATS_URL", "nats://host.containers.internal:4222")
            self.nc = NATS()
            await self.nc.connect(servers=[server_url])
            self.js = self.nc.jetstream()
            self.initialized = True
            logger.info("NATS Publisher initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize NATS Publisher: {e}")
            self.initialized = False


    async def publish_log(self, subject: str, log_data: dict):
        if not self.initialized:
            logger.error("Attempted to publish log but NATSPublisher is not initialized.") # Log error if not initialized
            raise RuntimeError("NATSPublisher not initialized. Call initialize() first.")
        try:
            message = json.dumps(log_data).encode()
            await self.js.publish(subject, message)
            logger.info(f"Successfully published log to subject: {subject}") # Log publish success
        except Exception as e:
            logger.error(f"Failed to publish log to subject {subject}: {e}") # Log publish failure
            # Optionally re-raise the exception if needed
            # raise e
