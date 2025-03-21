class Credentials:
    def __init__(self) -> None:
        self.credentials = []

    def add_credentials(self, username: str, password: str) -> None:
        self.credentials.append((username, password))

    def get_credentials(self) -> list:
        return self.credentials

    def remove_credentials(self, username: str, password: str) -> None:
        try:
            self.credentials.remove((username, password))
        except ValueError:
            pass

    def clear_credentials(self) -> None:
        self.credentials.clear()