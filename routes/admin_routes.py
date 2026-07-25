import re
import logging
from flask import Blueprint, render_template, request, redirect, url_for, session
from models.db_config import get_connection
from werkzeug.security import check_password_hash
from models.exam_questions import get_all_questions, get_question_by_id


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# --- LOGIN ---
@admin_bp.route("/login", methods=["GET", "POST"])

def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Adjust table name/schema to match your DB
            cursor.execute("SELECT * FROM dbo.UserLogin WHERE username=? AND password=?", (username, password))
            row = cursor.fetchone()
            conn.close()

            if row:
                session["admin_user"] = username  # mark logged in
                return redirect(url_for("admin.dashboard"))
            else:
                return render_template("index.html", error="Invalid credentials")
        except Exception as e:
            return render_template("index.html", error=f"Database error: {e}")
    else:
        # GET request → just show the login page
        return render_template("index.html")

@admin_bp.route("/dashboard", methods=["GET"])
def dashboard():
    if "admin_user" not in session:
        return redirect(url_for("admin.login"))
    # Render your admin dashboard template
    return render_template("admin_dashboard.html")

# --- ADD QUESTION ---
@admin_bp.route("/add-question", methods=["GET", "POST"])
def add_question():
    print("Request method:", request.method, "Path:", request.path)
    if "admin_user" not in session:
        return redirect(url_for("admin.login"))

    if request.method == "POST":
        section = request.form["section"]
        question_text = request.form.get("question_text")

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Check for duplicate
            cursor.execute(
                "SELECT 1 FROM ExamQuestions WHERE Section=? AND QuestionText=?",
                (section, question_text)
            )
            existing = cursor.fetchone()
            if existing:
                conn.close()
                return render_template("admin_form.html", error=f"Duplicate question in section {section}")

            # Insert new question
            cursor.execute("""
                INSERT INTO ExamQuestions
                (Section, QuestionText, QuestionImage,
                 OptionAText, OptionAImage,
                 OptionBText, OptionBImage,
                 OptionCText, OptionCImage,
                 OptionDText, OptionDImage,
                 CorrectOption)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                section,
                question_text,
                request.form.get("question_image"),
                request.form.get("option_a_text"),
                request.form.get("option_a_image"),
                request.form.get("option_b_text"),
                request.form.get("option_b_image"),
                request.form.get("option_c_text"),
                request.form.get("option_c_image"),
                request.form.get("option_d_text"),
                request.form.get("option_d_image"),
                request.form["correct_option"]
            ))

            conn.commit()
            conn.close()
            return redirect(url_for("admin.list_questions"))

        except Exception as e:
            conn.rollback()
            conn.close()
            return render_template("admin_form.html", error=f"Database error: {e}")

    # This must be aligned with the function, not inside try/except
    return render_template("admin_form.html")

@admin_bp.route("/list", methods=["GET"])
def list_questions():
    if "admin_user" not in session:
        # Require login first
        return redirect(url_for("admin.login"))

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Fetch all questions
        cursor.execute("""
            SELECT QuestionID, Section, QuestionText, QuestionImage,
                    OptionAText, OptionAImage,
                    OptionBText, OptionBImage,
                    OptionCText, OptionCImage,
                    OptionDText, OptionDImage,
                    CorrectOption
            FROM ExamQuestions
        """)
        rows = cursor.fetchall()
        conn.close()

        # Pass rows to template
        return render_template("currentquestionAfterLoad.html", questions=rows)

    except Exception as e:
        return render_template("currentquestionAfterLoad.html", error=f"Database error: {e}")


@admin_bp.route("/edit-question/<int:qid>", methods=["GET", "POST"])
def edit_question(qid):
    if "admin_user" not in session:
        return redirect(url_for("admin.login"))

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        # Update with new values
        cursor.execute("""
            UPDATE ExamQuestions
            SET Section=?, QuestionText=?, QuestionImage=?,
                OptionAText=?, OptionAImage=?,
                OptionBText=?, OptionBImage=?,
                OptionCText=?, OptionCImage=?,
                OptionDText=?, OptionDImage=?,
                CorrectOption=?
            WHERE QuestionID=?
        """, (
            request.form.get("section"),
            request.form.get("question_text"),
            request.form.get("question_image"),
            request.form.get("option_a_text"),
            request.form.get("option_a_image"),
            request.form.get("option_b_text"),
            request.form.get("option_b_image"),
            request.form.get("option_c_text"),
            request.form.get("option_c_image"),
            request.form.get("option_d_text"),
            request.form.get("option_d_image"),
            request.form.get("correct_option"),
            qid
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("admin.list_questions"))

    # GET → fetch existing record
    cursor.execute("""
        SELECT QuestionID, Section, QuestionText, QuestionImage,
                OptionAText, OptionAImage,
                OptionBText, OptionBImage,
                OptionCText, OptionCImage,
                OptionDText, OptionDImage,
                CorrectOption
        FROM ExamQuestions WHERE QuestionID=?
    """, (qid,))
    question = cursor.fetchone()
    conn.close()

    return render_template("edit_question.html", question=question)


 
