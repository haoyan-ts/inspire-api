"""Custom exceptions for Inspire Hand API."""


class InspireHandError(Exception):
    """Base exception for all Inspire Hand errors."""

    pass


class ConnectionError(InspireHandError):
    """Raised when connection to the hand fails or is lost."""

    pass


class RegisterError(InspireHandError):
    """Raised when register access fails or invalid register is accessed."""

    pass


class ValidationError(InspireHandError):
    """Raised when input validation fails."""

    pass


class HardwareError(InspireHandError):
    """Raised when hardware-specific errors occur."""

    pass


class CommunicationError(InspireHandError):
    """Raised when communication protocol errors occur."""

    pass


class TimeoutError(InspireHandError):
    """Raised when operation times out."""

    pass


class GenerationError(InspireHandError):
    """Raised when operation is not supported by hardware generation."""

    pass
