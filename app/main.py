import sys
import os
import uvicorn
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse # Added for sqlalchemy_integrity_error_handler
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError
from contextlib import asynccontextmanager

from app.api.v1 import api_router
from app.core.config import settings
from app.db.session import engine, check_db_connection
from app.db.base_class import Base
from app.models import * # noqa Ensure all models are imported for Base.metadata
from app.core.exceptions import (
    http_exception_handler,
    pydantic_validation_exception_handler,
    general_exception_handler,
)


def create_tables(): # For dev/testing
    print("Attempting to create database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created or already exist.")
    except Exception as e:
        print(f"Error creating database tables: {e}")

# create_tables() # Uncomment for auto-table creation on startup during development

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting up {settings.PROJECT_NAME}...")
    if check_db_connection():
        print("Database connection: OK")
        # create_tables() # If you want to ensure tables are created on startup
    else:
        print("CRITICAL: Database connection FAILED. Application functionality will be impaired.")
    yield
    # (Optional) Add shutdown logic here

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version="0.1.0",
    lifespan=lifespan,
)

# Exception Handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, pydantic_validation_exception_handler)
app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)

async def sqlalchemy_integrity_error_handler(request, exc: IntegrityError):
    # print(f"SQLAlchemy IntegrityError: {exc.orig}") # For debugging
    error_detail = "A database integrity error occurred. This might be due to a duplicate value for a unique field (e.g., email, slug, SKU)."
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": error_detail, "error_type": "IntegrityError", "db_error": str(exc.orig)},
    )
app.add_exception_handler(IntegrityError, sqlalchemy_integrity_error_handler)
app.add_exception_handler(Exception, general_exception_handler) # Catch-all


# CORS Middleware
if settings.BACKEND_CORS_ORIGINS:
    print(f"Configuring CORS for origins: {settings.BACKEND_CORS_ORIGINS}") # For debugging
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS, # Already a list of strings from config
        allow_credentials=True,
        allow_methods=["*"], # Allows all standard methods
        allow_headers=["*"], # Allows all headers
    )
else:
    print("Warning: No CORS origins configured. CORS will not be enabled.")


app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"])
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}! API available at {settings.API_V1_STR}. Visit /docs for interactive documentation."}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
