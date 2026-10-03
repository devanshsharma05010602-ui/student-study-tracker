"""
auth.py
-------
Authentication helpers for the Student Study & Progress Tracker.
Handles user registration, login, and session validation backed by SQLite.
"""

import hashlib
from database import init_db, get_user_by_username, create_user

# Ensure database and tables are created on start
init_db()


def _hash_password(password: str) -> str:
    """Return a SHA-256 hex digest of the given password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ================================================================== #
#  Public API                                                          #
# ================================================================== #

def user_exists(username: str) -> bool:
    """Return True if a user with the given username already exists."""
    return get_user_by_username(username) is not None


def register_user(username: str, password: str, full_name: str) -> tuple[bool, str]:
    """
    Register a new user in SQLite.

    Returns:
        (True, "")          on success.
        (False, error_msg)  on failure.
    """
    username  = username.strip()
    full_name = full_name.strip()

    if not username:
        return False, "Username cannot be empty."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if not password:
        return False, "Password cannot be empty."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if not full_name:
        return False, "Full name cannot be empty."
    if user_exists(username):
        return False, f"Username '{username}' is already taken."

    try:
        create_user(username, _hash_password(password), full_name)
        return True, ""
    except Exception as e:
        return False, f"Registration failed: {e}"


def login_user(username: str, password: str) -> tuple[bool, str, dict]:
    """
    Validate credentials against SQLite.

    Returns:
        (True,  "",          user_dict)  on success.
        (False, error_msg,   {})         on failure.
    """
    username = username.strip()
    user     = get_user_by_username(username)

    if not user:
        return False, "No account found with that username.", {}

    if user["password"] == _hash_password(password):
        # Return clean user dictionary without password
        return True, "", {
            "id"       : user["id"],
            "username" : user["username"],
            "full_name": user["full_name"],
        }

    return False, "Incorrect password.", {}
