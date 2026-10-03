"""
database.py
-----------
SQLite database management for the Student Study & Progress Tracker.
Handles table initialization, connections, and migrations from legacy JSON files.
"""

import sqlite3
import os
import json
from models import StudyTask

# Base directory: always relative to this file's folder, regardless of where Streamlit is launched
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "tracker.db")

DEFAULT_SUBJECTS = ["Python", "DBMS", "Linux", "DAA", "AIP"]


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database with row_factory and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Initialize all required tables in SQLite and migrate existing JSON data if present."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Subjects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, name)
            );
        """)

        # 3. Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                priority TEXT NOT NULL DEFAULT 'Medium',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        # 4. Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER PRIMARY KEY,
                student_name TEXT DEFAULT '',
                course TEXT DEFAULT 'MCA',
                semester TEXT DEFAULT 'Semester 1',
                daily_goal_hours INTEGER DEFAULT 4,
                target_completion_pct INTEGER DEFAULT 80,
                default_priority TEXT DEFAULT 'Medium',
                warn_below_target INTEGER DEFAULT 1,
                show_notes_col INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        conn.commit()

    # Attempt migration of legacy JSON data if database is fresh
    _migrate_legacy_data()


def _migrate_legacy_data() -> None:
    """Migrate legacy users.json, userdata/*.json, or root data.json into SQLite."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM users;")
        user_count = cursor.fetchone()["cnt"]

        # Only perform migration if users table is empty
        if user_count > 0:
            return

        users_file = os.path.join(BASE_DIR, "users.json")
        legacy_users = []
        if os.path.exists(users_file):
            try:
                with open(users_file, "r") as f:
                    legacy_users = json.load(f)
            except Exception:
                legacy_users = []

        # If legacy users existed, migrate them
        for u in legacy_users:
            uname = u.get("username", "").strip()
            pwd   = u.get("password", "")
            fname = u.get("full_name", "")
            if not uname or not pwd:
                continue

            cursor.execute(
                "INSERT OR IGNORE INTO users (username, password, full_name) VALUES (?, ?, ?);",
                (uname, pwd, fname)
            )
            user_id = cursor.lastrowid
            if not user_id:
                cursor.execute("SELECT id FROM users WHERE username = ?;", (uname,))
                row = cursor.fetchone()
                user_id = row["id"] if row else None

            if not user_id:
                continue

            # Check for user-specific data in userdata/
            safe_name = uname.lower().replace(" ", "_")
            user_data_file = os.path.join(BASE_DIR, "userdata", f"{safe_name}_data.json")
            user_settings_file = os.path.join(BASE_DIR, "userdata", f"{safe_name}_settings.json")

            subjects = DEFAULT_SUBJECTS
            tasks = []
            if os.path.exists(user_data_file):
                try:
                    with open(user_data_file, "r") as f:
                        d = json.load(f)
                        subjects = d.get("subjects", DEFAULT_SUBJECTS)
                        tasks = d.get("tasks", [])
                except Exception:
                    pass

            for s in subjects:
                cursor.execute(
                    "INSERT OR IGNORE INTO subjects (user_id, name) VALUES (?, ?);",
                    (user_id, s)
                )

            for t in tasks:
                cursor.execute("""
                    INSERT INTO tasks (user_id, task_id, subject, topic, status, priority, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (
                    user_id,
                    t.get("task_id", 1),
                    t.get("subject", ""),
                    t.get("topic", ""),
                    t.get("status", "Pending"),
                    t.get("priority", "Medium"),
                    t.get("notes", "")
                ))

            # Settings
            sett = {}
            if os.path.exists(user_settings_file):
                try:
                    with open(user_settings_file, "r") as f:
                        sett = json.load(f)
                except Exception:
                    pass

            cursor.execute("""
                INSERT OR REPLACE INTO settings (
                    user_id, student_name, course, semester, daily_goal_hours,
                    target_completion_pct, default_priority, warn_below_target, show_notes_col
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                user_id,
                sett.get("student_name", fname),
                sett.get("course", "MCA"),
                sett.get("semester", "Semester 1"),
                sett.get("daily_goal_hours", 4),
                sett.get("target_completion_pct", 80),
                sett.get("default_priority", "Medium"),
                1 if sett.get("warn_below_target", True) else 0,
                1 if sett.get("show_notes_col", True) else 0,
            ))

        conn.commit()


# ================================================================== #
#  User Management Queries                                             #
# ================================================================== #

def get_user_by_username(username: str) -> dict | None:
    """Fetch user by username (case-insensitive)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password, full_name FROM users WHERE username = ?;", (username.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_user(username: str, password_hash: str, full_name: str) -> int:
    """
    Create a new user, initialize their default subjects and settings,
    and seed any initial tasks from data.json if this is the first user.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, full_name) VALUES (?, ?, ?);",
            (username.strip(), password_hash, full_name.strip())
        )
        user_id = cursor.lastrowid

        # Initialize default subjects
        for sub in DEFAULT_SUBJECTS:
            cursor.execute(
                "INSERT OR IGNORE INTO subjects (user_id, name) VALUES (?, ?);",
                (user_id, sub)
            )

        # Initialize default settings
        cursor.execute("""
            INSERT INTO settings (
                user_id, student_name, course, semester, daily_goal_hours,
                target_completion_pct, default_priority, warn_below_target, show_notes_col
            ) VALUES (?, ?, 'MCA', 'Semester 1', 4, 80, 'Medium', 1, 1);
        """, (user_id, full_name.strip()))

        # Check if root data.json has legacy tasks to seed for this new user
        data_json_path = os.path.join(BASE_DIR, "data.json")
        if os.path.exists(data_json_path):
            try:
                with open(data_json_path, "r") as f:
                    legacy_data = json.load(f)
                legacy_tasks = legacy_data.get("tasks", [])
                for t in legacy_tasks:
                    cursor.execute("""
                        INSERT INTO tasks (user_id, task_id, subject, topic, status, priority, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?);
                    """, (
                        user_id,
                        t.get("task_id", 1),
                        t.get("subject", ""),
                        t.get("topic", ""),
                        t.get("status", "Pending"),
                        t.get("priority", "Medium"),
                        t.get("notes", "")
                    ))
            except Exception:
                pass

        conn.commit()
        return user_id


# ================================================================== #
#  Data Persistence Queries                                            #
# ================================================================== #

def get_user_data(username: str) -> tuple[list[str], list[StudyTask]]:
    """Retrieve subjects and StudyTask objects for a given username."""
    user = get_user_by_username(username)
    if not user:
        return DEFAULT_SUBJECTS.copy(), []

    user_id = user["id"]
    with get_connection() as conn:
        cursor = conn.cursor()

        # Load subjects
        cursor.execute("SELECT name FROM subjects WHERE user_id = ? ORDER BY id ASC;", (user_id,))
        subject_rows = cursor.fetchall()
        subjects = [row["name"] for row in subject_rows]
        if not subjects:
            subjects = DEFAULT_SUBJECTS.copy()

        # Load tasks
        cursor.execute("""
            SELECT task_id, subject, topic, status, priority, notes
            FROM tasks
            WHERE user_id = ?
            ORDER BY task_id ASC;
        """, (user_id,))
        task_rows = cursor.fetchall()
        tasks = [
            StudyTask(
                task_id  = r["task_id"],
                subject  = r["subject"],
                topic    = r["topic"],
                status   = r["status"],
                priority = r["priority"],
                notes    = r["notes"] or "",
            )
            for r in task_rows
        ]

    return subjects, tasks


def save_user_data(username: str, subjects: list[str], tasks: list[StudyTask]) -> None:
    """Save all subjects and tasks for a given username in SQLite atomically."""
    user = get_user_by_username(username)
    if not user:
        return

    user_id = user["id"]
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Replace subjects
        cursor.execute("DELETE FROM subjects WHERE user_id = ?;", (user_id,))
        for sub in subjects:
            cursor.execute(
                "INSERT INTO subjects (user_id, name) VALUES (?, ?);",
                (user_id, sub)
            )

        # 2. Replace tasks
        cursor.execute("DELETE FROM tasks WHERE user_id = ?;", (user_id,))
        for t in tasks:
            cursor.execute("""
                INSERT INTO tasks (user_id, task_id, subject, topic, status, priority, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (
                user_id,
                t.task_id,
                t.subject,
                t.topic,
                t.status,
                t.priority,
                t.notes,
            ))

        conn.commit()


# ================================================================== #
#  Settings Persistence Queries                                        #
# ================================================================== #

def get_user_settings(username: str) -> dict:
    """Retrieve settings dict for a given username."""
    user = get_user_by_username(username)
    if not user:
        return {}

    user_id = user["id"]
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT student_name, course, semester, daily_goal_hours,
                   target_completion_pct, default_priority, warn_below_target, show_notes_col
            FROM settings
            WHERE user_id = ?;
        """, (user_id,))
        row = cursor.fetchone()
        if not row:
            return {}

        return {
            "student_name"         : row["student_name"] or "",
            "course"               : row["course"] or "MCA",
            "semester"             : row["semester"] or "Semester 1",
            "daily_goal_hours"     : row["daily_goal_hours"],
            "target_completion_pct": row["target_completion_pct"],
            "default_priority"     : row["default_priority"] or "Medium",
            "warn_below_target"    : bool(row["warn_below_target"]),
            "show_notes_col"       : bool(row["show_notes_col"]),
        }


def save_user_settings(username: str, settings: dict) -> None:
    """Save settings dict for a given username in SQLite."""
    user = get_user_by_username(username)
    if not user:
        return

    user_id = user["id"]
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (
                user_id, student_name, course, semester, daily_goal_hours,
                target_completion_pct, default_priority, warn_below_target, show_notes_col
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            user_id,
            settings.get("student_name", ""),
            settings.get("course", "MCA"),
            settings.get("semester", "Semester 1"),
            settings.get("daily_goal_hours", 4),
            settings.get("target_completion_pct", 80),
            settings.get("default_priority", "Medium"),
            1 if settings.get("warn_below_target", True) else 0,
            1 if settings.get("show_notes_col", True) else 0,
        ))
        conn.commit()
