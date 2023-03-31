"""Exceptions used by Telenet."""


class TelenetException(Exception):
    """Base class for all exceptions raised by Telenet."""

    pass


class TelenetServiceException(Exception):
    """Raised when service is not available."""

    pass


class BadCredentialsException(Exception):
    """Raised when credentials are incorrect."""

    pass


class NotAuthenticatedException(Exception):
    """Raised when session is invalid."""

    pass


class GatewayTimeoutException(TelenetServiceException):
    """Raised when server times out."""

    pass


class BadGatewayException(TelenetServiceException):
    """Raised when server returns Bad Gateway."""

    pass
