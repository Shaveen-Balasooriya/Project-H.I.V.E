import asyncio
import json
from nats.aio.client import Client as NATS

async def main():
    async def log_handler(msg):
        data = json.loads(msg.data.decode())
        print("\n--- Log Received ---")
        for k, v in data.items():
            print(f"{k}: {v}")
        await msg.ack()

    nc = NATS()
    await nc.connect("nats://localhost:4222")
    js = nc.jetstream()

    await js.subscribe(
        "logs.honeypot",
        durable="log_collector",
        cb=log_handler,
        manual_ack=True
    )

    print("Log Collector is running... Listening for logs.")
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
