from Podman import Podman

def main() -> None:
    client = Podman()
    client.build_image('ssh')

if __name__ == '__main__':
    main()