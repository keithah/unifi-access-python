"""
UniFi Access Python SDK Exceptions

Custom exception classes for handling various error conditions when interacting
with the UniFi Access API.
"""


class UniFiAccessError(Exception):
    """Base exception for all UniFi Access API errors."""

    def __init__(
        self, message: str, status_code: int = None, response_data: dict = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(UniFiAccessError):
    """Raised when authentication fails or token is invalid."""

    pass


class ResourceNotFoundError(UniFiAccessError):
    """Raised when a requested resource is not found (404)."""

    pass


class ValidationError(UniFiAccessError):
    """Raised when request validation fails (400)."""

    pass


class APIError(UniFiAccessError):
    """Raised for general API errors (500, 503, etc.)."""

    pass


class RateLimitError(UniFiAccessError):
    """Raised when API rate limits are exceeded (429)."""

    pass


class PermissionError(UniFiAccessError):
    """Raised when user lacks permission for the requested operation (403)."""

    pass


class ConnectionError(UniFiAccessError):
    """Raised when unable to connect to the UniFi Access server."""

    pass


class TimeoutError(UniFiAccessError):
    """Raised when API requests timeout."""

    pass
