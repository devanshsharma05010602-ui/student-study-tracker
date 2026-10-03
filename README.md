# 📚 Student Study & Progress Tracker

A simple, functional web application built with **Python + Streamlit** to help students manage their study subjects, track topics, and monitor completion progress.

> **College Python Mini-Project**

---

## 🎯 Objective

Help students:
- Organise study subjects
- Add and track study tasks/topics
- Monitor overall and per-subject progress
- Search and filter tasks easily

---

## ✨ Features

| Feature | Description |
|---|---|
| **Dashboard** | Summary cards – total subjects, tasks, completed, pending, progress % |
| **Subject Management** | Add / remove subjects dynamically |
| **Task Management** | Add tasks with subject, topic, priority, notes |
| **Task Status** | Mark tasks as Pending or Completed |
| **Search** | Search tasks by topic keyword |
| **Filter** | Filter tasks by subject or status |
| **Progress Charts** | Bar chart (per subject) + Pie chart (overall) |
| **Data Persistence** | Relational data saved to SQLite database (`tracker.db`) — survives page refreshes and restarts |

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| **Python 3.x** | Main programming language |
| **Streamlit** | Web interface |
| **SQLite3** | Relational database & data persistence |
| **Pandas** | DataFrame display |
| **Matplotlib** | Progress charts |

---

## 📦 Installation

### 1. Clone / Download the project

```bash
# Navigate to the project folder
cd Student_Study_Tracker
```

### 2. (Optional) Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ How to Run

```bash
streamlit run app.py
```

The application will open automatically in your default web browser at `http://localhost:8501`.

---

## 📁 Project Structure

```
Student_Study_Tracker/
│
├── app.py           ← Main Streamlit application (UI + navigation)
├── models.py        ← StudyTask class (OOP)
├── functions.py     ← All business logic functions
├── data.json        ← Auto-created; stores subjects and tasks
├── requirements.txt ← Python package dependencies
└── README.md        ← This file
```

---

## 🐍 Python Concepts Demonstrated

### Variables & Data Types
- Strings, integers, floats, booleans used throughout

### Data Structures
- **Lists** – subjects list, tasks list
- **Dictionaries** – task data storage, summary stats, subject progress
- **List Comprehensions** – filtering and searching tasks

### Conditional Statements
```python
if total == 0:
    return 0.0   # Avoid division by zero
```

### Loops
```python
for task in tasks:
    if task.task_id == task_id:
        task.status = new_status
```

### Functions
```python
def add_subject(subjects, name)
def add_task(tasks, subject, topic, priority, notes)
def update_task_status(tasks, task_id, new_status)
def calculate_overall_progress(tasks)
def search_tasks(tasks, keyword)
def filter_tasks(tasks, subject, status)
```

### Object-Oriented Programming
```python
class StudyTask:
    def __init__(self, task_id, subject, topic, status, priority, notes):
        ...
    def mark_completed(self)
    def is_completed(self) -> bool
    def to_dict(self) -> dict
    def from_dict(cls, data) -> StudyTask   # classmethod
```

### File I/O
```python
with open("data.json", "w") as f:
    json.dump(raw, f, indent=4)
```

---

## 📸 Screenshots

After running the app, you will see:

- **Dashboard Tab** – Metric cards + subject progress bars + recent tasks  
- **Subjects Tab** – Add/remove subjects with task counts  
- **Study Tasks Tab** – Add tasks form + search/filter + task table + status update  
- **Progress Tab** – Horizontal bar chart + pie chart + stats table

---

## 👤 Author

Student Name: *(your name)*  
Course: MCA — Python Mini Project  
Year: 2026

---

## 📝 License

This project is for educational purposes only.
