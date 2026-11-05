
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash
)

import sqlite3
import database as db

app = Flask(__name__)
app.secret_key = "workshop-demo-key"


@app.route("/")
def home():
    summary = db.get_summary()
    books = db.get_books()

    return render_template(
        "index.html",
        books=books,
        summary=summary,
        query=""
    )


@app.route("/books")
def view_books():
    query = request.args.get("q", "").strip()
    books = db.search_books(query) if query else db.get_books()

    return render_template(
        "index.html",
        books=books,
        summary=db.get_summary(),
        query=query
    )


@app.route("/add", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        category = request.form.get("category", "").strip()

        try:
            quantity = int(request.form.get("quantity", "0"))
        except ValueError:
            quantity = -1

        if not title or not author or not category or quantity < 0:
            flash(
                "Enter valid book details and a non-negative quantity.",
                "error"
            )
        else:
            db.add_book(title, author, category, quantity)
            flash("Book added successfully.", "success")
            return redirect(url_for("home"))

    return render_template("add_book.html")


@app.route("/edit/<int:book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    book = db.get_book(book_id)

    if book is None:
        return "Book not found", 404

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        category = request.form.get("category", "").strip()

        try:
            quantity = int(request.form.get("quantity", "0"))
        except ValueError:
            quantity = -1

        if not title or not author or not category or quantity < 0:
            flash("Enter valid details.", "error")

        elif not db.update_book(
            book_id, title, author, category, quantity
        ):
            flash(
                "Quantity cannot be less than copies currently issued.",
                "error"
            )

        else:
            flash("Book updated successfully.", "success")
            return redirect(url_for("home"))

    return render_template("edit_book.html", book=book)


@app.route("/delete/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    if db.delete_book(book_id):
        flash("Book deleted.", "success")
    else:
        flash(
            "Return all issued copies before deleting this book.",
            "error"
        )

    return redirect(url_for("home"))


@app.route("/students", methods=["GET", "POST"])
def students():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        department = request.form.get("department", "").strip()
        email = request.form.get("email", "").strip()

        if name and department and email:
            try:
                db.add_student(name, department, email)
                flash("Student added successfully.", "success")
                return redirect(url_for("students"))

            except sqlite3.IntegrityError:
                flash("This email is already registered.", "error")

        else:
            flash("Complete all student fields.", "error")

    return render_template(
        "students.html",
        students=db.get_students()
    )


@app.route("/issue", methods=["GET", "POST"])
def issue():
    books = db.get_books()
    students_list = db.get_students()

    if request.method == "POST":
        try:
            book_id = int(request.form.get("book_id", "0"))
            student_id = int(request.form.get("student_id", "0"))

        except ValueError:
            flash("Select a valid book and student.", "error")
            return redirect(url_for("issue"))

        if db.issue_book(book_id, student_id):
            flash("Book issued successfully.", "success")
            return redirect(url_for("issued_books"))

        flash("Book unavailable or student/book not found.", "error")

    return render_template(
        "issue_book.html",
        books=books,
        students=students_list
    )


@app.route("/issued")
def issued_books():
    records = db.get_issue_records()

    return render_template(
        "issued_books.html",
        records=records
    )


@app.route("/return/<int:issue_id>", methods=["POST"])
def return_issued_book(issue_id):
    if db.return_book(issue_id):
        flash("Book returned successfully.", "success")
    else:
        flash(
            "This issue record is already returned or does not exist.",
            "error"
        )

    return redirect(url_for("issued_books"))


if __name__ == "__main__":
    app.run(debug=True)
