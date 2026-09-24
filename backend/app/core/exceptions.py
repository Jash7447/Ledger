class AppError(Exception):
    def __init__(self, detail: str, status_code: int) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class EmailAlreadyRegisteredError(AppError):
    def __init__(self) -> None:
        super().__init__("An account with this email already exists", 409)


class InvalidCredentialsError(AppError):
    def __init__(self) -> None:
        super().__init__("Incorrect email or password", 401)


class FinancialReferenceError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, 422)


class ResourceNotFoundError(AppError):
    def __init__(self, resource: str) -> None:
        super().__init__(f"{resource} not found", 404)


class ResourceConflictError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, 409)
