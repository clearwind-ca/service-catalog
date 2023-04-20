class CatalogError(Exception):
    """Base class for all catalog errors"""

    def __init__(self, message):
        self.message = message
        super().__init__(message)


class FetchError(CatalogError):
    """Base class for all GitHub fetching errors"""


class SendError(CatalogError):
    """Base class for all GitHub sending errors"""


class NoEntryFound(FetchError):
    """No entry found in the source for the catalog"""


class NoRepository(FetchError):
    """No repository at that address, or perhaps the user is unable to access it."""


class SchemaError(FetchError):
    """The JSON file doesn't match the schema"""


class PermissionError(SendError):
    """The user doesn't have permission to access the repository"""
