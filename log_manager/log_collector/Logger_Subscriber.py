import asyncio
import json
import sys
from nats.aio.client import Client as NATS
from nats.js.api import RetentionPolicy, AckPolicy, StreamConfig, ConsumerConfig, ReplayPolicy, DeliverPolicy

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

    # Ensure the stream exists first
    stream_name = "honeypot"
    stream_subject = "honeypot.logs"
    
    try:
        # Check if stream exists
        stream_info = await js.stream_info(stream_name)
        logging.info(f"Stream already exists: {stream_name}")
    except Exception as e:
        logging.info(f"Creating new stream: {stream_name}")
        # Create a StreamConfig object
        stream_config = StreamConfig(
            name=stream_name,
            subjects=[stream_subject],
            retention=RetentionPolicy.WORK_QUEUE,
            storage="file",
            max_age=60
        )
        await js.add_stream(config=stream_config)
        logging.info(f"Created stream: {stream_name} with subject: {stream_subject}")

    consumer_config = ConsumerConfig(
        durable_name="log-collector",
        ack_policy=AckPolicy.EXPLICIT,
        max_ack_pending=500,
        replay_policy=ReplayPolicy.INSTANT,
        deliver_policy=DeliverPolicy.ALL
    )

    # Use the same subject that was configured in the stream
    await js.subscribe(
        subject=stream_subject,
        durable="log-collector",
        cb=message_handler,
        config=consumer_config,
        manual_ack=True,
    )

    logging.info("[✓] Subscribed and listening...")
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
