import time
from credentials import Credentials
from Honeypots.SSH.ssh import SSHHoneypot

def main() -> None:
    credentials_maker = Credentials()
    credentials_maker.add_credentials('admin', 'admin')
    credentials_maker.add_credentials('user', 'user')

    ssh = SSHHoneypot(2222, 'OpenSSH_7.4p1 Ubuntu-10', credentials_maker.get_credentials())

    try:
        ssh.deploy()
        print('Honeypot deployed successfully!\n')
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('Stopping Honeypot...')
    finally:
        ssh.retract()
        print('Honeypot stopped successfully!')


if __name__ == '__main__':
    main()