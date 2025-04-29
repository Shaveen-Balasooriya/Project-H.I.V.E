import asyncio
import json
import sys
import logging
import os
import geoip2.database
from nats.aio.client import Client as NATS
from nats.js.api import RetentionPolicy, AckPolicy, StreamConfig, ConsumerConfig, ReplayPolicy, DeliverPolicy
from urllib.parse import urlparse
from opensearchpy import OpenSearch, exceptions as os_exceptions

# Basic logging setup
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Initialize GeoIP reader (open once)
geoip_reader = geoip2.database.Reader("/app/GeoLite2-City.mmdb")

# Environment variables for OpenSearch 
OPENSEARCH_URL = os.environ.get("OPENSEARCH_HOST")
OPENSEARCH_USER = os.environ.get("OPENSEARCH_USER")
OPENSEARCH_PASSWORD = os.environ.get("OPENSEARCH_PASSWORD")
NATS_URL = os.environ.get("NATS_URL")
INDEX_NAME = "hive-logs"


# Parse host URL and build OpenSearch client (HTTP, no SSL)
parsed = urlparse(OPENSEARCH_URL)
host = parsed.hostname or OPENSEARCH_URL
port = parsed.port or 9200
use_ssl = (parsed.scheme == "https")
client = OpenSearch(
    hosts=[{"host": host, "port": port}],
    http_auth=(OPENSEARCH_USER, OPENSEARCH_PASSWORD),
    use_ssl=use_ssl,
    verify_certs=False,
    ssl_show_warn=False,
    http_compress=True
)

# Define index settings and mappings for log data
INDEX_SETTINGS = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "honeypot_type":    { "type": "keyword" },
            "attacker_ip":      { "type": "ip"     },
            "attacker_port":    { "type": "integer" },
            "username":         { "type": "keyword" },
            "password":         { "type": "keyword" },
            "user-agent":       { "type": "keyword" },
            "time_of_entry":    { "type": "date"   },
            "time_of_exit":     { "type": "date"   },
            "commands_executed":{ "type": "keyword" },
            "duration_of_attack":{ "type": "integer" },
            "location": {
                "type": "geo_point"
            }
        }
    }
}

async def message_handler(msg):
    try:
        data = json.loads(msg.data.decode())
        attacker_ip = data.get("attacker_ip")
        
        # Calculate duration of attack
        entry_time = data.get("time_of_entry")
        exit_time = data.get("time_of_exit")
        if entry_time and exit_time:
            try:
                from datetime import datetime
                from dateutil import parser
                
                entry_datetime = parser.parse(entry_time)
                exit_datetime = parser.parse(exit_time)
                duration = exit_datetime - entry_datetime
                
                # Store duration in seconds
                data["duration_of_attack"] = int(duration.total_seconds())
            except Exception as e:
                logging.warning(f"Failed to calculate duration: {e}")
                data["duration_of_attack"] = 0
        
        # Get geolocation data (latitude/longitude)
        location = await lookup_geolocation(attacker_ip)
        if location:
            data["location"] = location
        
        logging.info(f"[Received and Enriched] {json.dumps(data, indent=2)}")

        # Index enriched log document (async to avoid blocking)
        await insert_into_opensearch(data)
        await msg.ack()
    except Exception as e:
        logging.error(f"Failed to process message: {e}")

async def lookup_geolocation(ip_address):
    try:
        response = geoip_reader.city(ip_address)
        return {
            "lat": response.location.latitude,
            "lon": response.location.longitude
        }
    except Exception as e:
        logging.warning(f"GeoIP lookup failed for {ip_address}: {e}")
        return None

async def insert_into_opensearch(document):
    try:
        # Index the document using the OpenSearch client (in a thread)
        result = await asyncio.to_thread(
            client.index,
            index=INDEX_NAME,
            body=document
        )
        doc_id = result.get('_id')
        logging.info(f"[✓] Indexed document (ID: {doc_id}) into '{INDEX_NAME}'")
    except Exception as e:
        logging.error(f"[✗] Failed to insert document: {e}")

async def main():
    # Ensure the index exists (create with mapping if not)
    try:
        if not await asyncio.to_thread(client.indices.exists, index=INDEX_NAME):
            await asyncio.to_thread(
                client.indices.create,
                INDEX_NAME,
                body=INDEX_SETTINGS
            )
            logging.info(f"[✓] Created index '{INDEX_NAME}' in OpenSearch")
        else:
            logging.info(f"Index '{INDEX_NAME}' already exists")
    except os_exceptions.AuthorizationException:
        logging.error("Unauthorized to create/check index (check credentials)")
    except Exception as e:
        logging.error(f"Error setting up index: {e}")

    # NATS/JetStream setup
    nc = NATS()
    await nc.connect(NATS_URL)
    js = nc.jetstream()

    stream_name = "honeypot"
    stream_subject = "honeypot.logs"

    try:
        await js.stream_info(stream_name)
        logging.info(f"Stream already exists: {stream_name}")
    except Exception:
        logging.info(f"Creating new stream: {stream_name}")
        stream_config = StreamConfig(
            name=stream_name,
            subjects=[stream_subject],
            retention=RetentionPolicy.WORK_QUEUE,
            storage="file",
            max_age=60
        )
        await js.add_stream(config=stream_config)
        logging.info(f"Created stream '{stream_name}' with subject '{stream_subject}'")

    consumer_config = ConsumerConfig(
        durable_name="log-collector",
        ack_policy=AckPolicy.EXPLICIT,
        max_ack_pending=500,
        replay_policy=ReplayPolicy.INSTANT,
        deliver_policy=DeliverPolicy.ALL
    )

    await js.subscribe(
        subject=stream_subject,
        durable="log-collector",
        cb=message_handler,
        config=consumer_config,
        manual_ack=True,
    )

    logging.info("[✓] Subscribed and listening for log messages...")
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        geoip_reader.close()
