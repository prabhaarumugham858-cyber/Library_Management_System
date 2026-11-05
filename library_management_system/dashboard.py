
import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="BookNest Analytics",
    page_icon="📚",
    layout="wide"
)

# Database path
DB_PATH = Path(__file__).resolve().parent / "library.db"

# Dashboard heading
st.title("📚 BookNest – Library Analytics")
st.caption("A live overview of books, students and borrowing activity.")


# Load database records
@st.cache_data(ttl=5)
def load_data():

    conn = sqlite3.connect(DB_PATH)

    books = pd.read_sql_query(
        "SELECT * FROM books ORDER BY title",
        conn
    )

    students = pd.read_sql_query(
        "SELECT * FROM students ORDER BY name",
        conn
    )

    issues = pd.read_sql_query("""
        SELECT
            issue_records.issue_id,
            books.title,
            students.name AS student_name,
            issue_records.issue_date,
            issue_records.return_date,
            issue_records.status
        FROM issue_records
        JOIN books
            ON issue_records.book_id = books.book_id
        JOIN students
            ON issue_records.student_id = students.student_id
        ORDER BY issue_records.issue_id DESC
    """, conn)

    conn.close()

    return books, students, issues


# Get data
books, students, issues = load_data()


# Calculate summary values
total_titles = len(books)

total_copies = (
    int(books["quantity"].sum())
    if not books.empty else 0
)

available = (
    int(books["available"].sum())
    if not books.empty else 0
)

issued = (
    int((issues["status"] == "Issued").sum())
    if not issues.empty else 0
)

returned = (
    int((issues["status"] == "Returned").sum())
    if not issues.empty else 0
)


# Display metrics
c1, c2, c3 = st.columns(3)

c1.metric("Book Titles", total_titles)
c2.metric("Total Copies", total_copies)
c3.metric("Available Copies", available)

c4, c5, c6 = st.columns(3)

c4.metric("Registered Students", len(students))
c5.metric("Currently Issued", issued)
c6.metric("Returned Records", returned)


st.divider()


# Charts section
left, right = st.columns(2)


with left:

    st.subheader("Book availability")

    if not books.empty:

        availability_data = books.set_index("title")[["available"]]

        st.bar_chart(availability_data)

    else:

        st.info("Add books through the Flask application.")


with right:

    st.subheader("Issue status")

    if not issues.empty:

        status_counts = (
            issues["status"]
            .value_counts()
            .rename_axis("Status")
            .to_frame("Records")
        )

        st.bar_chart(status_counts)

    else:

        st.info("No issue records available yet.")


st.divider()


# Book inventory
st.subheader("Book inventory")

if not books.empty:

    st.dataframe(
        books[
            [
                "book_id",
                "title",
                "author",
                "category",
                "quantity",
                "available"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

else:

    st.info("No books found.")


# Recent issue records
st.subheader("Recent issue records")

if not issues.empty:

    st.dataframe(
        issues,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info("No borrowing activity yet.")


st.divider()


# Footer
st.caption("BookNest | Built with Python, SQLite and Streamlit")


# Refresh dashboard
if st.button("Refresh dashboard"):

    st.cache_data.clear()
    st.rerun()
