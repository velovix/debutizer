class CommandError(Exception):
    """An error that suggests a mistake in the user's configuration or usage"""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = f"ERROR: {message}"


class UnexpectedError(Exception):
    """An error that suggests a bug in Debutizer"""

    def __init__(self, message: str):
        message += (
            "\n\nThis is likely a bug in Debutizer and not in your configuration. "
            "Please consider creating a bug report at "
            "https://github.com/velovix/debutizer/issues ."
        )
        super().__init__(message)
        self.message = message
