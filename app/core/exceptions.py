from fastapi import HTTPException, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from typing import Any, Optional
# Custom Exception Classes (Optional, but can be useful for specific error types)

class BaseCustomException(HTTPException):
    def __init__(self, status_code: int, detail: str = None, headers: dict = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class NotFoundException(BaseCustomException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class BadRequestException(BaseCustomException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class ForbiddenException(BaseCustomException):
    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class UnauthorizedException(BaseCustomException):
    def __init__(self, detail: str = "Authentication required", headers: dict = None):
        # Default WWW-Authenticate header for 401, can be overridden
        base_headers = {"WWW-Authenticate": "Bearer"}
        if headers:
            base_headers.update(headers)
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers=base_headers)

class UnprocessableEntityException(BaseCustomException):
    def __init__(self, detail: Any = "Unprocessable entity", errors: Optional[dict] = None):
        # Pydantic's ValidationError.errors() returns a list of dicts.
        # We can pass this along for more detailed client-side error handling.
        self.errors = errors or []
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


# Exception Handlers

async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Default handler for FastAPI's HTTPException.
    This can be customized if needed, but FastAPI handles it well by default.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )

async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    """
    Handler for Pydantic's ValidationError.
    This makes validation errors more user-friendly by returning a 422 status
    and a structured error message.
    """

    def clean_errors(errors):
        # Convierte cualquier valor bytes a string
        if isinstance(errors, list):
            for err in errors:
                if isinstance(err, dict):
                    for k, v in err.items():
                        if isinstance(v, bytes):
                            err[k] = v.decode(errors="replace")
        return errors

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": clean_errors(exc.errors())}
    )

async def general_exception_handler(request: Request, exc: Exception):
    """
    Handler for any other unhandled exceptions.
    This is a catch-all for unexpected errors, returning a 500 status.
    """
    # Log the exception for debugging purposes
    # import logging
    # logging.error(f"Unhandled exception: {exc}", exc_info=True)
    print(f"Unhandled exception: {exc}") # Basic print for now
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."},
    )

# You can add more specific handlers, e.g., for SQLAlchemy IntegrityError
# from sqlalchemy.exc import IntegrityError
# async def sqlalchemy_integrity_error_handler(request: Request, exc: IntegrityError):
#     # Determine if it's a unique constraint violation or other integrity issue
#     # Provide a user-friendly message
#     # This often results in a 400 or 409 (Conflict)
#     message = "Database integrity error."
#     # A more sophisticated check could be done here based on exc.orig (the DBAPI exception)
#     # For example, for psycopg2 unique violation:
#     # if isinstance(exc.orig, psycopg2.errors.UniqueViolation):
#     #    message = "A record with this value already exists."
#     #    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": message})
#     return JSONResponse(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         content={"detail": message}
#     )


# To be added to FastAPI app in main.py:
# from fastapi import FastAPI, Request, status
# from fastapi.exceptions import RequestValidationError # For Pydantic request body validation
# from pydantic import ValidationError # For Pydantic model validation (e.g. in responses, or manual validation)
# from starlette.exceptions import HTTPException as StarletteHTTPException

# from app.core.exceptions import (
#     http_exception_handler,
#     pydantic_validation_exception_handler,
#     general_exception_handler,
#     # sqlalchemy_integrity_error_handler
# )
# from sqlalchemy.exc import IntegrityError


# app.add_exception_handler(StarletteHTTPException, http_exception_handler)
# app.add_exception_handler(RequestValidationError, pydantic_validation_exception_handler) # Handles request body validation
# app.add_exception_handler(ValidationError, pydantic_validation_exception_handler) # Handles other Pydantic validation
# app.add_exception_handler(IntegrityError, sqlalchemy_integrity_error_handler) # Example for DB errors
# app.add_exception_handler(Exception, general_exception_handler) # Catch-all, should be last

