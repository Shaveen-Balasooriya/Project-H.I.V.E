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
            # Format the payload to match expected format from logger subscriber
            formatted_payload = self._format_payload(payload)
            message = json.dumps(formatted_payload).encode()
            await self.js.publish(self.subject_name, message)
            logger.info(f"Published log to {self.subject_name}: {formatted_payload.get('attacker_ip', 'unknown IP')}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    def _format_payload(self, payload: dict) -> dict:
        """Format the payload to match the expected structure by log subscriber"""
        # Make sure the keys match what's expected by the log subscriber
        formatted = {}
        
        # Map keys to the expected format
        if "ip" in payload:
            formatted["attacker_ip"] = payload["ip"]
        else:
            formatted["attacker_ip"] = payload.get("attacker_ip", "0.0.0.0")
            
        if "port" in payload:
            formatted["attacker_port"] = payload["port"]
        else:
            formatted["attacker_port"] = payload.get("attacker_port", 0)
            
        if "honeypot_type" not in payload:
            # Get honeypot type from environment or use "ftp" as default
            formatted["honeypot_type"] = os.getenv("HONEYPOT_TYPE", "ftp")
        else:
            formatted["honeypot_type"] = payload["honeypot_type"]
            
        # Ensure username and password are in the right format
        formatted["username"] = payload.get("username", "")
        formatted["password"] = payload.get("password", "")
        
        # Handle timestamps in ISO 8601 format
        if "entered_time" in payload:
            formatted["time_of_entry"] = self._ensure_iso_format(payload["entered_time"])
        else:
            formatted["time_of_entry"] = payload.get("time_of_entry", "")
            
        if "exited_time" in payload:
            formatted["time_of_exit"] = self._ensure_iso_format(payload["exited_time"])
        else:
            formatted["time_of_exit"] = payload.get("time_of_exit", "")
            
        # Handle user agent (may be empty for FTP)
        formatted["user-agent"] = payload.get("user_agent", payload.get("user-agent", ""))
        
        # Handle commands
        if "commands" in payload:
            formatted["commands_executed"] = payload["commands"]
        else:
            formatted["commands_executed"] = payload.get("commands_executed", [])
            
        # Transfer any other fields that might be relevant
        for key, value in payload.items():
            if key not in formatted and key not in ["ip", "port", "entered_time", "exited_time", "commands", "user_agent"]:
                formatted[key] = value
                
        return formatted
        
    def _ensure_iso_format(self, timestamp):
        """Ensure timestamp is in ISO 8601 format with Z suffix"""
        if timestamp and not timestamp.endswith('Z'):
            if 'T' in timestamp:
                return timestamp + 'Z'
            else:
                return timestamp.replace(' ', 'T') + 'Z'
        return timestamp

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