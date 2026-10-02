"""
functions.py
------------
All helper / business-logic functions for the Student Study & Progress Tracker.

Concepts demonstrated:
  - Functions with parameters and return values
  - List comprehensions
  - Dictionaries
  - Conditional statements
  - Loops
  - File I/O (JSON, CSV)
"""

import json
import os
import csv
import io
from models import StudyTask

# ---- Per-user data directory ---- #
USER_DATA_DIR = "userdata"   # folder that holds one data/settings file per user

# Default settings values
DEFAULT_SETTINGS: dict = {
    "student_name"         : "",
    "course"               : "MCA",
    "semester"             : "Semester 1",
    "daily_goal_hours"     : 4,
    "target_completion_pct": 80,
    "default_priority"     : "Medium",
    "warn_below_target"    : True,
    "show_notes_col"       : True,
}


# ================================================================== #
#  Data Persistence — Main Data                                        #
# ================================================================== #

def _data_path(username: str) -> str:
    """Return the path to a user's data JSON file."""
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    safe = username.lower().replace(" ", "_")
    return os.path.join(USER_DATA_DIR, f"{safe}_data.json")


def _settings_path(username: str) -> str:
    """Return the path to a user's settings JSON file."""
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    safe = username.lower().replace(" ", "_")
    return os.path.join(USER_DATA_DIR, f"{safe}_settings.json")


def load_data(username: str) -> tuple:
    """
    Load subjects and tasks from the user's JSON data file.

    Args:
        username (str): The logged-in user's username.

    Returns:
        subjects (list[str])      : List of subject names.
        tasks    (list[StudyTask]): List of StudyTask objects.
    """
    path = _data_path(username)
    if not os.path.exists(path):
        # Fresh account — return default subjects
        return ["Python", "DBMS", "Linux", "DAA", "AIP"], []

    with open(path, "r") as f:
        raw = json.load(f)

    subjects = raw.get("subjects", [])
    tasks    = [StudyTask.from_dict(t) for t in raw.get("tasks", [])]
    return subjects, tasks


def save_data(username: str, subjects: list, tasks: list) -> None:
    """
    Save subjects and tasks to the user's JSON data file.

    Args:
        username (str)            : The logged-in user's username.
        subjects (list[str])      : List of subject names.
        tasks    (list[StudyTask]): List of StudyTask objects.
    """
    raw = {
        "subjects": subjects,
        "tasks"   : [t.to_dict() for t in tasks],
    }
    with open(_data_path(username), "w") as f:
        json.dump(raw, f, indent=4)


# ================================================================== #
#  Data Persistence — Settings                                         #
# ================================================================== #

def load_settings(username: str) -> dict:
    """
    Load app settings from the user's settings JSON file.
    Missing keys are filled from DEFAULT_SETTINGS.

    Args:
        username (str): The logged-in user's username.

    Returns:
        settings (dict): Dictionary of all setting values.
    """
    path = _settings_path(username)
    if not os.path.exists(path):
        return DEFAULT_SETTINGS.copy()

    with open(path, "r") as f:
        saved = json.load(f)

    # Merge with defaults so new keys are always present
    settings = DEFAULT_SETTINGS.copy()
    settings.update(saved)
    return settings


def save_settings(username: str, settings: dict) -> None:
    """
    Save app settings to the user's settings JSON file.

    Args:
        username (str)   : The logged-in user's username.
        settings (dict)  : Dictionary of setting values to persist.
    """
    with open(_settings_path(username), "w") as f:
        json.dump(settings, f, indent=4)


# ================================================================== #
#  Subject Functions                                                   #
# ================================================================== #

def add_subject(subjects: list, name: str) -> tuple[list, str]:
    """
    Add a new subject to the subjects list.

    Args:
        subjects (list[str]): Existing list of subjects.
        name     (str)      : Name of the new subject.

    Returns:
        (updated_subjects, message)
    """
    name = name.strip()

    # Error handling: empty name
    if not name:
        return subjects, "❌ Subject name cannot be empty."

    # Error handling: duplicate subject
    if name in subjects:
        return subjects, f"❌ '{name}' already exists."

    subjects.append(name)
    return subjects, f"✅ Subject '{name}' added successfully!"


def remove_subject(subjects: list, tasks: list, name: str) -> tuple[list, list, str]:
    """
    Remove a subject and all its associated tasks.

    Args:
        subjects (list[str])      : Existing list of subjects.
        tasks    (list[StudyTask]): Existing list of tasks.
        name     (str)            : Name of the subject to remove.

    Returns:
        (updated_subjects, updated_tasks, message)
    """
    if name not in subjects:
        return subjects, tasks, f"❌ Subject '{name}' not found."

    subjects.remove(name)
    # Remove all tasks belonging to this subject using list comprehension
    tasks = [t for t in tasks if t.subject != name]
    return subjects, tasks, f"✅ Subject '{name}' and its tasks removed."


# ================================================================== #
#  Task Functions                                                      #
# ================================================================== #

def add_task(tasks: list, subject: str, topic: str,
             priority: str = "Medium", notes: str = "") -> tuple[list, str]:
    """
    Add a new study task.

    Args:
        tasks    (list[StudyTask]): Existing list of tasks.
        subject  (str)            : Subject for the task.
        topic    (str)            : Topic/task name.
        priority (str)            : Priority level.
        notes    (str)            : Optional notes.

    Returns:
        (updated_tasks, message)
    """
    topic = topic.strip()

    if not topic:
        return tasks, "❌ Topic name cannot be empty."

    if not subject:
        return tasks, "❌ Please select a subject."

    # Generate a new unique ID
    new_id = max((t.task_id for t in tasks), default=0) + 1

    new_task = StudyTask(
        task_id  = new_id,
        subject  = subject,
        topic    = topic,
        status   = "Pending",
        priority = priority,
        notes    = notes,
    )
    tasks.append(new_task)
    return tasks, f"✅ Task '{topic}' added under '{subject}'."


def update_task_status(tasks: list, task_id: int, new_status: str) -> list:
    """
    Update the status of a task.

    Args:
        tasks      (list[StudyTask]): List of tasks.
        task_id    (int)            : ID of the task to update.
        new_status (str)            : 'Pending' or 'Completed'.

    Returns:
        Updated list of tasks.
    """
    for task in tasks:
        if task.task_id == task_id:
            task.status = new_status
            break
    return tasks


def delete_task(tasks: list, task_id: int) -> tuple[list, str]:
    """
    Delete a task by its ID.

    Args:
        tasks   (list[StudyTask]): List of tasks.
        task_id (int)            : ID of the task to remove.

    Returns:
        (updated_tasks, message)
    """
    original_len = len(tasks)
    tasks = [t for t in tasks if t.task_id != task_id]

    if len(tasks) < original_len:
        return tasks, "✅ Task deleted."
    return tasks, "❌ Task not found."


def clear_completed_tasks(tasks: list) -> tuple[list, str]:
    """
    Remove all completed tasks from the list.

    Args:
        tasks (list[StudyTask]): All tasks.

    Returns:
        (updated_tasks, message)
    """
    pending_only = [t for t in tasks if not t.is_completed()]
    removed      = len(tasks) - len(pending_only)

    if removed == 0:
        return tasks, "ℹ️ No completed tasks to remove."
    return pending_only, f"✅ Removed {removed} completed task(s)."


def mark_all_tasks(tasks: list, subject: str, new_status: str) -> tuple[list, str]:
    """
    Mark all tasks of a specific subject as Completed or Pending.

    Args:
        tasks      (list[StudyTask]): All tasks.
        subject    (str)            : Subject name ('All' for every subject).
        new_status (str)            : 'Pending' or 'Completed'.

    Returns:
        (updated_tasks, message)
    """
    count = 0
    for task in tasks:
        if subject == "All" or task.subject == subject:
            task.status = new_status
            count += 1

    scope = subject if subject != "All" else "all subjects"
    return tasks, f"✅ Marked {count} task(s) in {scope} as {new_status}."


# ================================================================== #
#  Search & Filter Functions                                           #
# ================================================================== #

def search_tasks(tasks: list, keyword: str) -> list:
    """
    Search tasks by topic name (case-insensitive).

    Args:
        tasks   (list[StudyTask]): List of tasks to search.
        keyword (str)            : Search keyword.

    Returns:
        List of matching StudyTask objects.
    """
    keyword = keyword.strip().lower()
    if not keyword:
        return tasks

    # List comprehension to filter tasks
    return [t for t in tasks if keyword in t.topic.lower()]


def filter_tasks(tasks: list, subject: str = "All",
                 status: str = "All") -> list:
    """
    Filter tasks by subject and/or status.

    Args:
        tasks   (list[StudyTask]): List of tasks.
        subject (str)            : Subject to filter by, or 'All'.
        status  (str)            : Status to filter by, or 'All'.

    Returns:
        Filtered list of StudyTask objects.
    """
    result = tasks

    if subject != "All":
        result = [t for t in result if t.subject == subject]

    if status != "All":
        result = [t for t in result if t.status == status]

    return result


# ================================================================== #
#  Progress Calculation                                                #
# ================================================================== #

def calculate_overall_progress(tasks: list) -> float:
    """
    Calculate overall completion percentage across all tasks.

    Progress = (Completed Tasks / Total Tasks) * 100

    Args:
        tasks (list[StudyTask]): All tasks.

    Returns:
        Progress as a float (0.0 to 100.0).
    """
    total = len(tasks)
    if total == 0:
        return 0.0  # Avoid division by zero

    completed = sum(1 for t in tasks if t.is_completed())
    return round((completed / total) * 100, 1)


def calculate_subject_progress(tasks: list, subject: str) -> dict:
    """
    Calculate progress for a specific subject.

    Args:
        tasks   (list[StudyTask]): All tasks.
        subject (str)            : Subject name.

    Returns:
        Dictionary with 'total', 'completed', 'percentage' keys.
    """
    subject_tasks = [t for t in tasks if t.subject == subject]
    total         = len(subject_tasks)
    completed     = sum(1 for t in subject_tasks if t.is_completed())
    percentage    = round((completed / total) * 100, 1) if total > 0 else 0.0

    return {
        "total"     : total,
        "completed" : completed,
        "percentage": percentage,
    }


def get_all_subject_progress(subjects: list, tasks: list) -> list:
    """
    Return progress data for every subject.

    Args:
        subjects (list[str])      : List of subject names.
        tasks    (list[StudyTask]): All tasks.

    Returns:
        List of dicts with keys: 'subject', 'total', 'completed', 'percentage'.
    """
    result = []
    for subject in subjects:
        progress = calculate_subject_progress(tasks, subject)
        result.append({
            "subject"   : subject,
            "total"     : progress["total"],
            "completed" : progress["completed"],
            "percentage": progress["percentage"],
        })
    return result


# ================================================================== #
#  Summary Statistics                                                  #
# ================================================================== #

def get_summary_stats(subjects: list, tasks: list) -> dict:
    """
    Return a summary dictionary for the dashboard.

    Args:
        subjects (list[str])      : List of subjects.
        tasks    (list[StudyTask]): All tasks.

    Returns:
        Dictionary with summary statistics.
    """
    total_subjects = len(subjects)
    total_tasks    = len(tasks)
    completed      = sum(1 for t in tasks if t.is_completed())
    pending        = total_tasks - completed
    progress       = calculate_overall_progress(tasks)

    return {
        "total_subjects": total_subjects,
        "total_tasks"   : total_tasks,
        "completed"     : completed,
        "pending"       : pending,
        "progress"      : progress,
    }


# ================================================================== #
#  Export Functions                                                    #
# ================================================================== #

def export_tasks_csv(tasks: list) -> str:
    """
    Export all tasks to a CSV-formatted string for download.

    Args:
        tasks (list[StudyTask]): All tasks to export.

    Returns:
        A CSV string that can be written to a file.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header row
    writer.writerow(["Task ID", "Subject", "Topic", "Status", "Priority", "Notes"])

    # Write each task as a row using a loop
    for task in tasks:
        writer.writerow([
            task.task_id,
            task.subject,
            task.topic,
            task.status,
            task.priority,
            task.notes,
        ])

    return output.getvalue()


def export_data_json(subjects: list, tasks: list) -> str:
    """
    Export all app data (subjects + tasks) as a pretty-printed JSON string.

    Args:
        subjects (list[str])      : List of subjects.
        tasks    (list[StudyTask]): All tasks.

    Returns:
        A JSON-formatted string.
    """
    raw = {
        "subjects": subjects,
        "tasks"   : [t.to_dict() for t in tasks],
    }
    return json.dumps(raw, indent=4)


def get_priority_summary(tasks: list) -> dict:
    """
    Count tasks grouped by priority level.

    Args:
        tasks (list[StudyTask]): All tasks.

    Returns:
        Dict with keys 'High', 'Medium', 'Low' and their counts.
    """
    summary = {"High": 0, "Medium": 0, "Low": 0}
    for task in tasks:
        if task.priority in summary:
            summary[task.priority] += 1
    return summary
