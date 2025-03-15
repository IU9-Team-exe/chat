import secrets
from argon2 import PasswordHasher

def hash_password(password, salt, secret_factor):
    ph = PasswordHasher()
    return ph.hash(password + salt + secret_factor)

def verify_password(hashed, password, salt, secret_factor):
    ph = PasswordHasher()
    try:
        return ph.verify(hashed, password + salt + secret_factor)
    except Exception:
        return False

if __name__ == "__main__":
    salt = secrets.token_urlsafe(16)
    secret_factor = "bmstu"
    password = "StrongPassword123"
    hashed_password = hash_password(password, salt, secret_factor)
    print("Hashed Password:", hashed_password)
    password_input = input("Введите пароль: ")
    is_valid = verify_password(hashed_password, password_input, salt, secret_factor)
    if is_valid:
        print("Password is correct!")
    else:
        print("Password is incorrect.")
