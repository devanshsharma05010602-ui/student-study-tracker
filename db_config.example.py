"""
db_config.example.py
--------------------
Template database configuration settings for MySQL.
Copy or rename this file to 'db_config.py' and enter your local MySQL credentials.
"""

import os

MYSQL_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "port": int(os.environ.get("MYSQL_PORT", 3306)),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),  # Enter your MySQL root password here
    "database": os.environ.get("MYSQL_DATABASE", "student_tracker"),
    "charset": "utf8mb4",
    "use_unicode": True,
}
