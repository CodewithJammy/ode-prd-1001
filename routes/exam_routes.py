import logging
from flask import Blueprint, render_template, request, session, redirect, url_for,jsonify
from models.db_config import get_connection

# Create blueprint
exam_bp = Blueprint("exam", __name__, url_prefix="/exam")

# --- LOGIN ---
@exam_bp.route("/login", methods=["GET", "POST"])

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
                session["exam_user"] = username  # mark logged in
                return redirect(url_for("exam.exam_home"))
            else:
                return render_template("index.html", error="Invalid credentials")
        except Exception as e:
            return render_template("index.html", error=f"Database error: {e}")
    else:
        # GET request → just show the login page
        return render_template("index.html")

# --- Exam Home Page ---
@exam_bp.route("/", methods=["GET"])
def exam_home():
    if "exam_user" not in session:
        # If you want only logged-in users to access exam
        return redirect(url_for("admin.login"))

    return render_template("practice.html")  # your HTML page


# --- Load Questions by Section ---
@exam_bp.route("/questions/<string:section>", methods=["GET"])
def get_questions(section):
    section_map = {
    "quant": "Quantitative Aptitude",
    "logical": "Logical Reasoning",
    "verbal": "Verbal Ability",
    "coding": "Coding"
     }
    db_section = section_map.get(section, section)
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT QuestionID, QuestionText, QuestionImage,
                   OptionAText, OptionAImage,
                   OptionBText, OptionBImage,
                   OptionCText, OptionCImage,
                   OptionDText, OptionDImage,
                   CorrectOption
            FROM ExamQuestions
            WHERE Section = ?
        """, (db_section,))
        rows = cursor.fetchall()
        conn.close()

        questions = []
        for row in rows:
            questions.append({
                "id": row[0],
                "text": row[1],
                "image": row[2],
                "options": {
                    "A": {"text": row[3], "image": row[4]},
                    "B": {"text": row[5], "image": row[6]},
                    "C": {"text": row[7], "image": row[8]},
                    "D": {"text": row[9], "image": row[10]},
                },
                "correct": row[11]
            })

        return jsonify({"section": section, "questions": questions})

    except Exception as e:
        return jsonify({"error": str(e)})

# --- Submit Answer ---
@exam_bp.route("/submit/<int:qid>", methods=["POST"])
def submit_answer(qid):
    selected_option = request.form.get("selected_option")
    # You can store answers in session or DB
    answers = session.get("answers", {})
    answers[qid] = selected_option
    session["answers"] = answers

    return redirect(url_for("exam.exam_home"))
