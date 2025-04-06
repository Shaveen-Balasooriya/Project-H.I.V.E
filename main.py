import time
from honeypot_manager.honeypot_manager import HoneypotManager
from honeypot_manager.Honeypot import Honeypot


def main() -> None:
    honeypot = Honeypot()
    print('Creating Honeypot...')
    honeypot.create_honeypot('ssh', 2222)
    print('Starting Honeypot...')
    honeypot.start_honeypot()
    print('Fetching all Honeypots...')
    honeypots = HoneypotManager()
    h = honeypots.fetch_all_honeypots()
    for honey in h:
        print(f'Honeypot Name: {honey.honeypot_name}')
        print(f'Honeypot Status: {honey.honeypot_status}')
        print(f'Honeypot Type: {honey.honeypot_type}')
        print(f'Honeypot Port: {honey.honeypot_port}')
        print('-------------------')
if __name__ == '__main__':
    main()