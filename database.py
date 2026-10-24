"""
database.py
-----------
MySQL database management for the Student Study & Progress Tracker.
Handles table initialization, connections, and migrations.
Configuration is loaded from db_config.py.
"""

import os
import json
import mysql.connector
from models import StudyTask

try:
    from db_config import MYSQL_CONFIG
except ImportError:
    MYSQL_CONFIG = {
        "host": os.environ.get("MYSQL_HOST", "localhost"),
        "port": int(os.environ.get("MYSQL_PORT", 3306)),
        "user": os.environ.get("MYSQL_USER", "root"),
        "password": os.environ.get("MYSQL_PASSWORD", ""),
        "database": os.environ.get("MYSQL_DATABASE", "student_tracker"),
        "charset": "utf8mb4",
        "use_unicode": True,
    }

# Base directory: relative to this file's folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_SUBJECTS = ["Python", "DBMS", "Linux", "DAA", "AIP"]


def get_connection():
    """Return an active connection to MySQL with autocommit enabled."""
    return mysql.connector.connect(
        host=MYSQL_CONFIG["host"],
        port=MYSQL_CONFIG["port"],
        user=MYSQL_CONFIG["user"],
        password=MYSQL_CONFIG["password"],
        database=MYSQL_CONFIG["database"],
        charset=MYSQL_CONFIG.get("charset", "utf8mb4"),
        autocommit=True,
    )


try:
    import streamlit as st
except ImportError:
    st = None


def init_db() -> None:
    """
    Ensure the MySQL database and all required tables exist.
    Also migrates existing JSON data if the database is freshly created.
    """
    try:
        # 1. Ensure the target database exists on MySQL server
        root_config = MYSQL_CONFIG.copy()
        db_name = root_config.pop("database", "student_tracker")

        try:
            pre_conn = mysql.connector.connect(**root_config, autocommit=True)
            pre_cursor = pre_conn.cursor()
            pre_cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
            pre_cursor.close()
            pre_conn.close()
        except Exception as e:
            print(f"[database.py] Notice during database check: {e}")

        # 2. Connect to the database and initialize required tables
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True, buffered=True)

            # 1. Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    full_name VARCHAR(150) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 2. Subjects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE KEY uq_user_subject (user_id, name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 3. Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    task_id INT NOT NULL,
                    subject VARCHAR(100) NOT NULL,
                    topic VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'Pending',
                    priority VARCHAR(50) NOT NULL DEFAULT 'Medium',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 4. Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    user_id INT PRIMARY KEY,
                    student_name VARCHAR(150) DEFAULT '',
                    course VARCHAR(100) DEFAULT 'MCA',
                    semester VARCHAR(100) DEFAULT 'Semester 1',
                    daily_goal_hours INT DEFAULT 4,
                    target_completion_pct INT DEFAULT 80,
                    default_priority VARCHAR(50) DEFAULT 'Medium',
                    warn_below_target TINYINT DEFAULT 1,
                    show_notes_col TINYINT DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            cursor.close()

        # Attempt migration of legacy JSON data if database is fresh
        _migrate_legacy_data()

    except mysql.connector.Error as err:
        err_msg = (
            f"MySQL Connection Error [{err.errno}]: {err.msg}\n"
            "Please check host, port, user, and password in db_config.py."
        )
        print(f"[database.py ERROR] {err_msg}")
        if st is not None:
            try:
                st.error(f"⚠️ {err_msg}")
            except Exception:
                pass


def _migrate_legacy_data() -> None:
    """Migrate legacy users.json, userdata/*.json, or root data.json into MySQL."""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT COUNT(*) as cnt FROM users;")
        row = cursor.fetchone()
        user_count = row["cnt"] if row else 0

        # Only perform migration if users table is empty
        if user_count > 0:
            cursor.close()
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
                "INSERT IGNORE INTO users (username, password, full_name) VALUES (%s, %s, %s);",
                (uname, pwd, fname)
            )
            user_id = cursor.lastrowid
            if not user_id:
                cursor.execute("SELECT id FROM users WHERE username = %s;", (uname,))
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
                    "INSERT IGNORE INTO subjects (user_id, name) VALUES (%s, %s);",
                    (user_id, s)
                )

            for t in tasks:
                cursor.execute("""
                    INSERT INTO tasks (user_id, task_id, subject, topic, status, priority, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
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
                REPLACE INTO settings (
                    user_id, student_name, course, semester, daily_goal_hours,
                    target_completion_pct, default_priority, warn_below_target, show_notes_col
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
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

        cursor.close()


# ================================================================== #
#  User Management Queries                                             #
# ================================================================== #

def get_user_by_username(username: str) -> dict | None:
    """Fetch user by username (case-insensitive by default in MySQL)."""
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT id, username, password, full_name FROM users WHERE username = %s;", (username.strip(),))
        row = cursor.fetchone()
        cursor.close()
        return dict(row) if row else None


def create_user(username: str, password_hash: str, full_name: str) -> int:
    """
    Create a new user, initialize their default subjects and settings,
    and seed any initial tasks from data.json if this is the first user.
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute(
            "INSERT INTO users (username, password, full_name) VALUES (%s, %s, %s);",
            (username.strip(), password_hash, full_name.strip())
        )
        user_id = cursor.lastrowid

        # Initialize default subjects
        for sub in DEFAULT_SUBJECTS:
            cursor.execute(
                "INSERT IGNORE INTO subjects (user_id, name) VALUES (%s, %s);",
                (user_id, sub)
            )

        # Initialize default settings
        cursor.execute("""
            INSERT INTO settings (
                user_id, student_name, course, semester, daily_goal_hours,
                target_completion_pct, default_priority, warn_below_target, show_notes_col
            ) VALUES (%s, %s, 'MCA', 'Semester 1', 4, 80, 'Medium', 1, 1);
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
                        VALUES (%s, %s, %s, %s, %s, %s, %s);
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

        cursor.close()
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
        cursor = conn.cursor(dictionary=True, buffered=True)

        # Load subjects
        cursor.execute("SELECT name FROM subjects WHERE user_id = %s ORDER BY id ASC;", (user_id,))
        subject_rows = cursor.fetchall()
        subjects = [row["name"] for row in subject_rows]
        if not subjects:
            subjects = DEFAULT_SUBJECTS.copy()

        # Load tasks
        cursor.execute("""
            SELECT task_id, subject, topic, status, priority, notes
            FROM tasks
            WHERE user_id = %s
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
        cursor.close()

    return subjects, tasks


def save_user_data(username: str, subjects: list[str], tasks: list[StudyTask]) -> None:
    """Save all subjects and tasks for a given username in MySQL atomically."""
    user = get_user_by_username(username)
    if not user:
        return

    user_id = user["id"]
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True, buffered=True)

        # 1. Replace subjects
        cursor.execute("DELETE FROM subjects WHERE user_id = %s;", (user_id,))
        for sub in subjects:
            cursor.execute(
                "INSERT INTO subjects (user_id, name) VALUES (%s, %s);",
                (user_id, sub)
            )

        # 2. Replace tasks
        cursor.execute("DELETE FROM tasks WHERE user_id = %s;", (user_id,))
        for t in tasks:
            cursor.execute("""
                INSERT INTO tasks (user_id, task_id, subject, topic, status, priority, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (
                user_id,
                t.task_id,
                t.subject,
                t.topic,
                t.status,
                t.priority,
                t.notes,
            ))

        cursor.close()


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
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("""
            SELECT student_name, course, semester, daily_goal_hours,
                   target_completion_pct, default_priority, warn_below_target, show_notes_col
            FROM settings
            WHERE user_id = %s;
        """, (user_id,))
        row = cursor.fetchone()
        cursor.close()
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
    """Save settings dict for a given username in MySQL."""
    user = get_user_by_username(username)
    if not user:
        return

    user_id = user["id"]
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("""
            REPLACE INTO settings (
                user_id, student_name, course, semester, daily_goal_hours,
                target_completion_pct, default_priority, warn_below_target, show_notes_col
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
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
        cursor.close()
