import podman

def build_image(client) -> None:
    try:
        print('Building SSH Honeypot...')
        client.images.build(path='./Honeypots/SSH', tag='SSH-Honeypot', rm=True)
        print('Done!')
    except Exception as e:
        print(f'Error building image: {str(e)}')

def main() -> None:
    try:
        # Connect to the Podman API
        client = podman.PodmanClient(base_url='tcp://localhost:8888')  # Adjust if needed
        # Check if Podman is running
        if client.ping():
            print('Connected to Podman and service is running')
            build_image(client=client)
        else:
            print('Connected to Podman but service is not running')
    except Exception as e:
        print(f'Error: {str(e)}')


if __name__ == "__main__":
    main()