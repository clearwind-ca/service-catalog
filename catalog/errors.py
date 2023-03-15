class FetchError(Exception):
    """Base class for all catalog errors"""

    def __init__(self, message):
        self.message = message
        super().__init__(message)


class NoEntryFound(FetchError):
    """No entry found in the source for the catalog"""


class NoRepository(FetchError):
    """No repository at that address, or perhaps the user is unable to access it."""


class SchemaError(FetchError):
    """The JSON file doesn't match the schema"""
