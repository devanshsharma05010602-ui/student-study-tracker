"""
models.py
---------
Contains the data model classes used in the Student Study & Progress Tracker.

Concepts demonstrated:
  - Object-Oriented Programming (OOP)
  - Classes and objects
  - Methods
  - __str__ / __repr__
"""


class StudyTask:
    """
    Represents a single study task/topic for a subject.

    Attributes:
        task_id  (int)  : Unique identifier for the task.
        subject  (str)  : Name of the subject this task belongs to.
        topic    (str)  : Name of the topic/task.
        status   (str)  : 'Pending' or 'Completed'.
        priority (str)  : 'Low', 'Medium', or 'High'.
        notes    (str)  : Optional notes about the task.
    """

    def __init__(self, task_id: int, subject: str, topic: str,
                 status: str = "Pending", priority: str = "Medium",
                 notes: str = ""):
        self.task_id  = task_id
        self.subject  = subject
        self.topic    = topic
        self.status   = status   # 'Pending' or 'Completed'
        self.priority = priority # 'Low', 'Medium', 'High'
        self.notes    = notes

    # ------------------------------------------------------------------ #
    #  Methods                                                             #
    # ------------------------------------------------------------------ #

    def mark_completed(self):
        """Mark this task as Completed."""
        self.status = "Completed"

    def mark_pending(self):
        """Mark this task as Pending."""
        self.status = "Pending"

    def is_completed(self) -> bool:
        """Return True if the task is completed."""
        return self.status == "Completed"

    def get_status_icon(self) -> str:
        """Return a visual icon based on current status."""
        return "✓" if self.is_completed() else "○"

    def to_dict(self) -> dict:
        """Convert the task to a dictionary (for JSON storage)."""
        return {
            "task_id" : self.task_id,
            "subject" : self.subject,
            "topic"   : self.topic,
            "status"  : self.status,
            "priority": self.priority,
            "notes"   : self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StudyTask":
        """Create a StudyTask object from a dictionary (loaded from JSON)."""
        return cls(
            task_id  = data["task_id"],
            subject  = data["subject"],
            topic    = data["topic"],
            status   = data.get("status",   "Pending"),
            priority = data.get("priority", "Medium"),
            notes    = data.get("notes",    ""),
        )

    def __str__(self) -> str:
        return (f"{self.get_status_icon()} [{self.subject}] "
                f"{self.topic} — {self.status} ({self.priority})")

    def __repr__(self) -> str:
        return f"StudyTask(id={self.task_id}, subject={self.subject!r}, topic={self.topic!r})"
