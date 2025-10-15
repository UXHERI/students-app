import os
import random
import sqlite3
from pathlib import Path
from typing import List

from flask import Flask, render_template, request, redirect, url_for, flash


BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / "students.db"
STATIC_DIR = BASE_DIR / "static"

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(STATIC_DIR),
)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")


def get_db_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
              roll_no TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              email TEXT NOT NULL,
              contact TEXT NOT NULL,
              gender TEXT NOT NULL CHECK (gender IN ('Male','Female')),
              avatar TEXT NOT NULL,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()


def list_avatar_files_for_gender(gender: str) -> List[str]:
    gender_dir = STATIC_DIR / "img" / ("male" if gender == "Male" else "female")
    if not gender_dir.exists():
        return []
    allowed_exts = {".svg", ".png", ".jpg", ".jpeg", ".gif"}
    files = [f.name for f in sorted(gender_dir.iterdir()) if f.suffix.lower() in allowed_exts]
    return files


def choose_random_avatar(gender: str) -> str:
    files = list_avatar_files_for_gender(gender)
    if not files:
        # Fallback to a generic placeholder if no images are available
        return f"img/{'male' if gender == 'Male' else 'female'}/placeholder.svg"
    return f"img/{'male' if gender == 'Male' else 'female'}/{random.choice(files)}"


@app.get("/")
def index():
    with get_db_connection() as connection:
        students = connection.execute(
            "SELECT roll_no, name, email, contact, gender, avatar, created_at FROM students ORDER BY datetime(created_at) DESC"
        ).fetchall()
    return render_template("index.html", students=students)


@app.post("/add")
def add_student():
    name = (request.form.get("name") or "").strip()
    roll_no = (request.form.get("roll_no") or "").strip()
    email = (request.form.get("email") or "").strip()
    contact = (request.form.get("contact") or "").strip()
    gender = (request.form.get("gender") or "").strip().capitalize()

    if gender not in {"Male", "Female"}:
        flash("Please choose a valid gender.", "error")
        return redirect(url_for("index"))

    missing = [label for label, value in {
        "Name": name,
        "Roll No.": roll_no,
        "Email": email,
        "Contact": contact,
    }.items() if not value]

    if missing:
        flash(f"Missing required fields: {', '.join(missing)}", "error")
        return redirect(url_for("index"))

    avatar_rel_path = choose_random_avatar(gender)

    try:
        with get_db_connection() as connection:
            connection.execute(
                """
                INSERT INTO students (roll_no, name, email, contact, gender, avatar)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (roll_no, name, email, contact, gender, avatar_rel_path),
            )
            connection.commit()
        flash("Student added successfully!", "success")
    except sqlite3.IntegrityError:
        flash("Roll No. already exists.", "error")
    except Exception as exc:  # pragma: no cover
        flash(f"Unexpected error: {exc}", "error")

    return redirect(url_for("index"))


# Initialize database eagerly so tables exist in all run modes
initialize_database()


if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
