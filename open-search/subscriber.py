import asyncio
import json
from nats.aio.client import Client as NATS
from opensearchpy import OpenSearch

# OpenSearch client initialization (same as before)
client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    http_compress=True,  # optional
    http_auth=("admin", "Strong_Password123!"),
    use_ssl=True,
    verify_certs=False,  # <- Important: self-signed SSL cert
    ssl_show_warn=False,  # <- Optional: don't spam SSL warnings
)

async def run_subscriber():
    nc = NATS()
    await nc.connect("nats://127.0.0.1:4222")
    js = nc.jetstream()

    # Make sure the stream exists (should have been created by publisher, but just in case)
    await js.add_stream(name="HONEYPOT", subjects=["honeypot.logs"])

    # Create/subscribe a durable consumer to the "HONEYPOT" stream
    # Durable name ensures if our subscriber disconnects, it can resume from last read.
    sub = await js.subscribe("honeypot.logs", durable="HONEYPOT_DURABLE")

    print("Subscribed to honeypot.logs, waiting for messages...")
    # Consume messages in a loop
    try:
        async for msg in sub.messages:
            data = msg.data.decode()
            log_entry = json.loads(data)
            print(f"Received log: {log_entry}")

            # Index the log into OpenSearch
            try:
                res = client.index(index="honeypot-logs", body=log_entry)
                # Optionally, check res['result'] == 'created' or 'indexed'
                print(f"Indexed to OpenSearch (ID: {res['_id']})")
            except Exception as e:
                print(f"Error indexing to OpenSearch: {e}")

            # Acknowledge the message to JetStream (mark as processed)
            await msg.ack()
    except Exception as e:
        print(f"Subscriber encountered an error: {e}")

if __name__ == "__main__":
    asyncio.run(run_subscriber())
