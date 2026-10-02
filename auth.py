"""
auth.py
-------
Authentication helpers for the Student Study & Progress Tracker.
Handles user registration, login, and session management.

Credentials are stored in users.json (plain JSON — no external deps).
Each entry: { "username": "...", "password": "...", "full_name": "..." }
"""

import json
import os
import hashlib

USERS_FILE = "users.json"


# ================================================================== #
#  Internal helpers                                                    #
# ================================================================== #

def _hash_password(password: str) -> str:
    """Return a SHA-256 hex digest of the given password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _load_users() -> list:
    """Load all registered users from the JSON file."""
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def _save_users(users: list) -> None:
    """Persist the user list to disk."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


# ================================================================== #
#  Public API                                                          #
# ================================================================== #

def user_exists(username: str) -> bool:
    """Return True if a user with the given username already exists."""
    users = _load_users()
    return any(u["username"].lower() == username.lower() for u in users)


def register_user(username: str, password: str, full_name: str) -> tuple:
    """
    Register a new user.

    Returns:
        (True, "")          on success.
        (False, error_msg)  on failure.
    """
    username = username.strip()
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

    users = _load_users()
    users.append({
        "username" : username,
        "password" : _hash_password(password),
        "full_name": full_name,
    })
    _save_users(users)
    return True, ""


def login_user(username: str, password: str) -> tuple:
    """
    Validate credentials.

    Returns:
        (True,  "",          user_dict)  on success.
        (False, error_msg,   {})         on failure.
    """
    username = username.strip()
    users    = _load_users()

    for u in users:
        if u["username"].lower() == username.lower():
            if u["password"] == _hash_password(password):
                return True, "", u
            return False, "Incorrect password.", {}

    return False, "No account found with that username.", {}
