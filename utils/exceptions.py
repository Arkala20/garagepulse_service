"""
utils/exceptions.py

Custom exception classes for GaragePulse.
Used across services, controllers, and repositories.
"""


class ApplicationError(Exception):
    """
    Base exception for all application-specific errors.
    """

    def __init__(self, message: str = "An unexpected application error occurred"):
        super().__init__(message)
        self.message = message


class ValidationError(ApplicationError):
    """
    Raised when input validation fails.
    """

    def __init__(self, message: str = "Invalid input provided"):
        super().__init__(message)


class AuthenticationError(ApplicationError):
    """
    Raised when authentication fails.
    Example: wrong password, user not found
    """

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class AuthorizationError(ApplicationError):
    """
    Raised when user does not have permission.
    """

    def __init__(self, message: str = "You are not authorized to perform this action"):
        super().__init__(message)


class NotFoundError(ApplicationError):
    """
    Raised when a requested resource is not found.
    """

    def __init__(self, message: str = "Requested resource not found"):
        super().__init__(message)


class DatabaseError(ApplicationError):
    """
    Raised for database-related issues.
    """

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message)


class ConflictError(ApplicationError):
    """
    Raised when a duplicate or conflicting record exists.
    Example: duplicate email/username
    """

    def __init__(self, message: str = "Conflict with existing data"):
        super().__init__(message)


class BusinessRuleError(ApplicationError):
    """
    Raised when business logic rules are violated.
    Example: activating already active account
    """

    def __init__(self, message: str = "Business rule violation"):
        super().__init__(message)