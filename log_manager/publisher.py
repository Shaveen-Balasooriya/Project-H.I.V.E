import asyncio
import json
import datetime
import random
from nats.aio.client import Client as NATS

HONEYPOT_TYPES = ["ssh", "ftp", "http"]
USERNAMES = ["admin", "root", "guest", "test"]
PASSWORDS = ["admin123", "password", "123456", "qwerty"]
COMMAND_SETS = [
    ["ls", "pwd", "free"],
    ["whoami", "uname -a", "cat /etc/passwd"],
    ["cd /tmp", "touch hacked.txt", "ls -l"],
]

# Collection of real public DNS servers and IP addresses from around the world
ATTACKER_IPS = [
    "8.8.8.8",         # Google DNS (USA)
    "8.8.4.4",         # Google DNS Secondary (USA)
    "1.1.1.1",         # Cloudflare DNS (Global)
    "1.0.0.1",         # Cloudflare DNS Secondary (Global)
    "9.9.9.9",         # Quad9 DNS (Global)
    "208.67.222.222",  # OpenDNS (USA)
    "208.67.220.220",  # OpenDNS Secondary (USA)
    "64.6.64.6",       # Verisign DNS (USA)
    "64.6.65.6",       # Verisign DNS Secondary (USA)
    "77.88.8.8",       # Yandex DNS (Russia)
    "77.88.8.1",       # Yandex DNS Secondary (Russia)
    "114.114.114.114", # 114DNS (China)
    "114.114.115.115", # 114DNS Secondary (China)
    "119.29.29.29",    # DNSPod (China)
    "180.76.76.76",    # Baidu DNS (China)
    "203.80.96.10",    # Hong Kong DNS
    "195.46.39.39",    # SafeDNS (Russia)
    "195.46.39.40",    # SafeDNS Secondary (Russia)
    "84.200.69.80",    # DNS.WATCH (Germany)
    "84.200.70.40",    # DNS.WATCH Secondary (Germany)
    "103.86.96.100",   # India DNS
    "103.86.99.100",   # India DNS Secondary
    "2001:4860:4860::8888", # Google DNS IPv6
    "2606:4700:4700::1111", # Cloudflare IPv6
]

def generate_log():
    entry_time = datetime.datetime.utcnow()
    exit_time = entry_time + datetime.timedelta(minutes=random.randint(1, 5))

    return {
        "honeypot_type": random.choice(HONEYPOT_TYPES),
        "attacker_ip": random.choice(ATTACKER_IPS),
        "attacker_port": random.randint(1024, 65535),
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "username": random.choice(USERNAMES),
        "password": random.choice(PASSWORDS),
        "time_of_entry": entry_time.isoformat() + "Z",  # ISO 8601 format
        "time_of_exit": exit_time.isoformat() + "Z",
        "commands_executed": random.choice(COMMAND_SETS),
    }

async def publish_forever():
    nc = NATS()
    await nc.connect("nats://hive-nats-server:4222")  # connect inside hive-net by hostname
    js = nc.jetstream()

    # Ensure stream exists
    try:
        await js.stream_info("honeypot")
    except:
        await js.add_stream(name="honeypot", subjects=["honeypot.logs"])

    print("[✓] Publisher connected. Publishing logs...")

    while True:
        log_data = generate_log()
        await js.publish("honeypot.logs", json.dumps(log_data).encode())
        print(f"[Published] {log_data}")
        await asyncio.sleep(2)  # Publish every 2 seconds

if __name__ == "__main__":
    asyncio.run(publish_forever())
