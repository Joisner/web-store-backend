# FastAPI E-commerce Backend

This is the backend for the e-commerce application, built with FastAPI and MySQL.

## Features

*   User registration and JWT authentication (login, refresh tokens).
*   CRUD operations for Products, Categories, and Users.
*   Modular structure with services, schemas (Pydantic), and models (SQLAlchemy).
*   Basic pagination and filtering for product listings.
*   CORS configuration.
*   Initial set of unit and integration tests.

## Setup Instructions

1.  **Prerequisites:**
    *   Python 3.8+
    *   MySQL Server
    *   Virtual environment tool (e.g., `venv`)

2.  **Clone the repository (if applicable, otherwise navigate to the `backend` directory).**
    The `backend` code is expected to be in a directory named `backend` at the root of the project.

3.  **Create and activate a virtual environment *inside the `backend` directory*:**
    ```bash
    cd backend
    python -m venv venv
    ```
    *   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```
    (If you created the venv outside `backend`, adjust paths accordingly for activation and running commands).

4.  **Install dependencies (ensure you are in the `backend` directory with venv active):**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Set up environment variables (in the `backend` directory):**
    *   Copy `.env.example` to a new file named `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file with your actual database credentials:
        *   `DATABASE_URL`: e.g., `mysql+pymysql://user:password@host:port/dbname`
        *   `SECRET_KEY`: Generate a strong secret key (e.g., using `openssl rand -hex 32`).
        *   `BACKEND_CORS_ORIGINS`: Comma-separated list of allowed frontend origins (e.g., `http://localhost:4200`).

6.  **Database Setup:**
    *   Ensure your MySQL server is running.
    *   Create a database with the name specified in your `DATABASE_URL` (e.g., `fastapi_db` if using the default in `.env.example`).
    *   **Table Creation:**
        *   The application **does not** automatically create tables on startup by default in `app/main.py` for production safety.
        *   For development, you can uncomment the `create_tables()` call within the `startup_event` in `app/main.py`. This function is defined in `app/main.py` and uses SQLAlchemy's `Base.metadata.create_all(bind=engine)`.
        *   A more robust approach for production is to use database migrations (e.g., with Alembic), which are not yet implemented in this project.

## Running the Application

1.  **Ensure your virtual environment is activated (from within the `backend` directory) and the `.env` file is configured.**
2.  **Start the FastAPI development server (from the `backend` directory):**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    The application will be available at `http://127.0.0.1:8000` (or `http://localhost:8000`).
    Interactive API documentation (Swagger UI) will be at `http://127.0.0.1:8000/docs`.
    Alternative API documentation (ReDoc) will be at `http://127.0.0.1:8000/redoc`.

## Running Tests

1.  **Ensure your virtual environment is activated (from within the `backend` directory) and test dependencies are installed (they are in `requirements.txt`).**
2.  **Configure a separate test database URL if desired.**
    The tests in `tests/conftest.py` are configured to append `_test` to your `DATABASE_URL` from `.env` (e.g., `fastapi_db_test`). Ensure this test database exists and the user has permissions.
    Alternatively, modify `TEST_DATABASE_URL` logic in `tests/conftest.py` or set `DATABASE_URL` in `pytest.ini` (or via environment variables that `pytest.ini` might load if configured to do so).
3.  **Run pytest from the `backend` directory:**
    ```bash
    pytest -v
    ```
    To include coverage reports:
    ```bash
    pytest -v --cov=app --cov-report=html --cov-report=term
    ```
    The HTML coverage report will be in `htmlcov/index.html`.

    **Note on Test Execution:** If you encounter `ModuleNotFoundError` (e.g., for `fastapi` or other dependencies) when running tests:
    *   Confirm you are running `pytest` from the `backend` directory.
    *   Verify that your virtual environment (created inside `backend`) is activated and that `pip install -r requirements.txt` was successful within this venv. `pytest` must be using this venv's Python interpreter and packages.

## Project Structure

(Located within the `backend` directory)
```
.
├── app/
│   ├── api/                  # API routers and endpoints
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/    # Specific endpoint modules (auth, users, products, categories)
│   ├── auth/                 # Authentication related logic (currently empty, core logic in services/security)
│   ├── core/                 # Core components (config, security, exceptions)
│   ├── db/                   # Database session, base model, engine
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic schemas (data validation & serialization)
│   ├── services/             # Business logic (CRUD operations, etc.)
│   ├── utils/                # Utility functions (e.g., slugify)
│   ├── __init__.py
│   └── main.py               # FastAPI app initialization, main router, startup events, CORS
├── tests/                    # Test suite
│   ├── api/                  # API endpoint tests
│   ├── services/             # Service layer tests
│   ├── utils/                # Utility function tests
│   ├── __init__.py
│   └── conftest.py           # Pytest configuration and fixtures
├── .env.example              # Example environment variables
├── pytest.ini                # Pytest configuration
├── README.md                 # This file
└── requirements.txt          # Python dependencies
```

## Further Development & TODOs

*   Implement Alembic for database migrations.
*   Enhance authorization logic (e.g., role-based access control for certain endpoints).
*   Add more comprehensive tests, especially for edge cases and service logic.
*   Implement image uploading to a storage service instead of just storing URLs.
*   Refine product variant and inventory management (e.g., stock updates on variant level).
*   Add more complex filtering and searching capabilities for products.
*   Integrate logging more thoroughly throughout the application.
*   Consider background tasks for long-running operations (e.g., sending emails on registration).
```
