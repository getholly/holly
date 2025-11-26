class UnsupportedModelError(Exception):
    """Exception for unsupported model configurations."""


class MissingGeminiKeyError(Exception):
    pass


class TextLengthError(Exception):
    """Exception for text that is too short."""

    default_message = "Text is too short to process, must be at least 1 character"

    def __init__(self, message=None):
        super().__init__(message or self.default_message)
