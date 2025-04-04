from Podman import Podman

def main() -> None:
    client = Podman()
    honeypot = client.create_honeypot(honeypot_type='ssh'.lower(), port_to_bind=2222)
    client.start_honeypot()
if __name__ == '__main__':
    main()