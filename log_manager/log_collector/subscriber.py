import asyncio
import json
import sys
from nats.aio.client import Client as NATS

# Configure logging to print to stdout
import logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

async def message_handler(msg):
    try:
        data = json.loads(msg.data.decode())
        logging.info(f"Received message: {data}")
        await msg.ack()  # Acknowledge the message
    except Exception as e:
        logging.error(f"Failed to process message: {e}")

async def main():
    nc = NATS()
    await nc.connect("nats://hive-nats-server:4222")
    js = nc.jetstream()

    # Create stream if not already created
    try:
        await js.add_stream(
            name="honeypot",
            subjects=["honeypot.logs"],
            retention="workqueue",
            storage="file",
            max_age=60 # 1GB
        )
    except Exception as e:
        logging.error(f"Stream may already exist: {e}")

    await js.subscribe(
        "honeypot.logs",
        cb=message_handler,
        durable="log-collector",
        manual_ack=True
    )

    logging.info("[✓] Subscribed and listening...")
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
