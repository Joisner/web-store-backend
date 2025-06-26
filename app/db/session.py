from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from typing import Generator

# Para SQL Server 2022, asegúrate que tu DATABASE_URL tenga el formato:
# mssql+pyodbc://user:password@server:port/database?driver=ODBC+Driver+18+for+SQL+Server
# Ejemplo:
# DATABASE_URL = "mssql+pyodbc://sa:your_password@localhost:1433/your_db?driver=ODBC+Driver+18+for+SQL+Server"

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    # echo=True # Uncomment for debugging SQL in development
    connect_args={"TrustServerCertificate": "yes"}  # Opcional: evita problemas de SSL en desarrollo
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get a database session.
    Ensures the session is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Optional: A function to test the database connection
def check_db_connection():
    try:
        # Try to connect to the database
        with engine.connect() as connection:
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

# Optional: A function to create all tables (useful for initial setup or tests)
# from app.db.base_class import Base # Ensure Base is imported if you use this
# from app.models import * # Ensure all your models are imported
# def init_db():
#     Base.metadata.create_all(bind=engine)

# if __name__ == "__main__":
#     if check_db_connection():
#         print("Database connection successful.")
#         # You could initialize the DB here if running this script directly
#         # print("Initializing database tables...")
#         # init_db()
#         # print("Database tables initialized.")
#     else:
#         print("Database connection could not be established.")
