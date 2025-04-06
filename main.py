import time
from Honeypot import Honeypot

def main() -> None:
    honeypot = Honeypot()
    print('Creating Honeypot...')
    honeypot.create_honeypot('ssh', 2222)
    print(honeypot.honeypot_status)
    time.sleep(1)
    print('Starting Honeypot...')
    honeypot.start_honeypot()
    print(honeypot.honeypot_status)
    time.sleep(10)
    print('Stopping Honeypot...')
    honeypot.stop_honeypot()
    print(honeypot.honeypot_status)
    print('Deleting Honeypot...')
    honeypot.remove_honeypot()
    print(honeypot.honeypot_status)

if __name__ == '__main__':
    main()