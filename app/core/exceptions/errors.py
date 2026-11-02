class AppError(Exception):
    """Base exceptions for all application errors."""


class NotFoundError(AppError):
    """Raise when a resource is not found."""
    def __init__(self, resource: str, key: str):
        super().__init__(f"'{resource}' not found with key '{key}'")


class ConflictError(AppError):
    """Raise when a resource conflict occurs."""
    def __init__(self, resource: str, key: str):
        super().__init__(f"Conflict with '{resource}' and key '{key}'")

        