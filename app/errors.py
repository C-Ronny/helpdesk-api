"""
Application-level exceptions
Services raise these instead of HTTP errors
A single handler in main.py converts them to responses.
"""

class AppError(Exception):
    status_code = 400
    code = "BAD_REQUEST"

    def __init__(self, detail: str, code: str | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        if code is not None:
            self.code = code


class NotFoundError(AppError):
    """The referenced resource does not exist."""
    status_code = 404
    code = "NOT_FOUND"


class ForbiddenError(AppError):
    """The request was understood but the caller's role does not permit it."""
    status_code = 403
    code = "FORBIDDEN"


class BusinessRuleError(AppError):
    """A well-formed request that violates a domain rule."""
    status_code = 400
    code = "BUSINESS_RULE_VIOLATION"


class ConflictError(AppError):
    """The request is valid but the resource is in an incompatible state."""
    status_code = 409
    code = "CONFLICT"