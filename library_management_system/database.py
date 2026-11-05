
import sqlite3
from pathlib import Path
from datetime import date

DB_PATH = Path(__file__).resolve().parent / "library.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity >= 0),
            available INTEGER NOT NULL CHECK(available >= 0)
        );

        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS issue_records (
            issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL,
            return_date TEXT,
            status TEXT NOT NULL DEFAULT 'Issued',
            FOREIGN KEY(book_id) REFERENCES books(book_id),
            FOREIGN KEY(student_id) REFERENCES students(student_id)
        );
        """)


def get_books():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM books ORDER BY book_id DESC"
        ).fetchall()


def get_book(book_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM books WHERE book_id = ?",
            (book_id,)
        ).fetchone()


def add_book(title, author, category, quantity):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO books
            (title, author, category, quantity, available)
            VALUES (?, ?, ?, ?, ?)""",
            (title, author, category, quantity, quantity)
        )


def update_book(book_id, title, author, category, quantity):
    with get_connection() as conn:
        book = conn.execute(
            "SELECT quantity, available FROM books WHERE book_id = ?",
            (book_id,)
        ).fetchone()

        if book is None:
            return False

        issued_count = book["quantity"] - book["available"]

        if quantity < issued_count:
            return False

        available = quantity - issued_count

        conn.execute(
            """UPDATE books
            SET title = ?, author = ?, category = ?,
                quantity = ?, available = ?
            WHERE book_id = ?""",
            (title, author, category, quantity, available, book_id)
        )

        return True


def delete_book(book_id):
    with get_connection() as conn:
        active = conn.execute(
            """SELECT COUNT(*) FROM issue_records
            WHERE book_id = ? AND status = 'Issued'""",
            (book_id,)
        ).fetchone()[0]

        if active:
            return False

        conn.execute(
            "DELETE FROM issue_records WHERE book_id = ?",
            (book_id,)
        )

        conn.execute(
            "DELETE FROM books WHERE book_id = ?",
            (book_id,)
        )

        return True


def search_books(keyword):
    pattern = f"%{keyword}%"

    with get_connection() as conn:
        return conn.execute(
            """SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ? OR category LIKE ?
            ORDER BY title""",
            (pattern, pattern, pattern)
        ).fetchall()


def add_student(name, department, email):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO students (name, department, email)
            VALUES (?, ?, ?)""",
            (name, department, email)
        )


def get_students():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM students ORDER BY name"
        ).fetchall()


def issue_book(book_id, student_id):
    with get_connection() as conn:
        book = conn.execute(
            "SELECT available FROM books WHERE book_id = ?",
            (book_id,)
        ).fetchone()

        student = conn.execute(
            "SELECT student_id FROM students WHERE student_id = ?",
            (student_id,)
        ).fetchone()

        if book is None or student is None or book["available"] < 1:
            return False

        conn.execute(
            """INSERT INTO issue_records
            (book_id, student_id, issue_date, status)
            VALUES (?, ?, ?, 'Issued')""",
            (book_id, student_id, date.today().isoformat())
        )

        conn.execute(
            "UPDATE books SET available = available - 1 WHERE book_id = ?",
            (book_id,)
        )

        return True


def get_issue_records():
    with get_connection() as conn:
        return conn.execute("""
        SELECT issue_records.issue_id,
               books.title,
               students.name,
               students.department,
               issue_records.issue_date,
               issue_records.return_date,
               issue_records.status
        FROM issue_records
        JOIN books ON issue_records.book_id = books.book_id
        JOIN students ON issue_records.student_id = students.student_id
        ORDER BY issue_records.issue_id DESC
        """).fetchall()


def return_book(issue_id):
    with get_connection() as conn:
        record = conn.execute(
            """SELECT book_id FROM issue_records
            WHERE issue_id = ? AND status = 'Issued'""",
            (issue_id,)
        ).fetchone()

        if record is None:
            return False

        conn.execute(
            """UPDATE issue_records
            SET status = 'Returned', return_date = ?
            WHERE issue_id = ?""",
            (date.today().isoformat(), issue_id)
        )

        conn.execute(
            "UPDATE books SET available = available + 1 WHERE book_id = ?",
            (record["book_id"],)
        )

        return True


def get_summary():
    with get_connection() as conn:
        books = conn.execute("""
        SELECT COUNT(*) AS titles,
               COALESCE(SUM(quantity), 0) AS copies,
               COALESCE(SUM(available), 0) AS available
        FROM books
        """).fetchone()

        students = conn.execute(
            "SELECT COUNT(*) FROM students"
        ).fetchone()[0]

        issued = conn.execute(
            "SELECT COUNT(*) FROM issue_records WHERE status = 'Issued'"
        ).fetchone()[0]

        returned = conn.execute(
            "SELECT COUNT(*) FROM issue_records WHERE status = 'Returned'"
        ).fetchone()[0]

        return {
            "titles": books["titles"],
            "copies": books["copies"],
            "available": books["available"],
            "students": students,
            "issued": issued,
            "returned": returned
        }


create_tables()
