from podman_control.Podman import Podman

def main() -> None:
    client = Podman()
    client.check_config()

if __name__ == '__main__':
    main()