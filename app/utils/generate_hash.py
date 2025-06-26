from app.core.security import get_password_hash

if __name__ == "__main__":
    print(get_password_hash("123456"))
