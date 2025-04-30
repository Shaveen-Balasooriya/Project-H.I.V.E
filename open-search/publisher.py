import asyncio
import json
import datetime
from nats.aio.client import Client as NATS

# Sample data for simulation
HONEYPOT_TYPES = ["ssh", "ftp", "ssh", "http"]  # weighted towards ssh for example
USERNAMES = ["root", "admin", "guest", "oracle"]
PASSWORDS = ["123456", "password", "admin", "toor", "111111"]
COMMANDS = ["uname -a", "id", "ls", "echo 'hello'", "cat /etc/passwd"]

# Function to simulate generating a random log
import random
def generate_log():
    hp_type = random.choice(HONEYPOT_TYPES)
    log = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "honeypot": hp_type,
        "attacker_ip": f"203.0.113.{random.randint(1,254)}",  # using TEST-NET-3 range for example
        "attacker_port": 22 if hp_type == "ssh" else (80 if hp_type == "web" else 3306),
        "user_agent": "N/A" if hp_type != "web" else "Mozilla/5.0",  # user agent only for web
        "username": random.choice(USERNAMES),
        "password": random.choice(PASSWORDS),
        "commands": random.choice(COMMANDS) if hp_type != "web" else f"GET /index.php?{random.randint(100,999)}",
        "country": random.choice(["US", "CN", "RU", "IN", "DE"])  # random country
    }
    return log

async def run_publisher():
    # Connect to NATS
    nc = NATS()
    await nc.connect("nats://127.0.0.1:4222")
    js = nc.jetstream()  # JetStream context

    # Ensure a JetStream stream exists to persist the messages (optional)
    # Define a stream that listens on 'honeypot.logs' subject
    await js.add_stream(name="HONEYPOT", subjects=["honeypot.logs"])

    print("Publishing honeypot log messages...")
    # Publish messages in a loop
    while True:
        log_entry = generate_log()
        # Convert to JSON bytes
        msg_data = json.dumps(log_entry).encode('utf-8')
        # Publish to the subject via JetStream
        ack = await js.publish("honeypot.logs", msg_data)
        # (ack has seq number, etc., we can log it if needed)
        print(f"Published log seq={ack.seq}: {log_entry}")
        # wait for a second before sending next (adjust as needed for volume)
        await asyncio.sleep(1)

    # Note: this loop will run indefinitely. In a real scenario, you might run for a certain time or number of messages.

# Run the publisher indefinitely (press Ctrl+C to stop)
if __name__ == "__main__":
    asyncio.run(run_publisher())
