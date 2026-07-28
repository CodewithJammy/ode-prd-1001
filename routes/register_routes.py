import pyodbc
from flask import Flask, Blueprint, render_template, request, session, redirect, url_for,jsonify
from models.db_config import get_connection
from werkzeug.security import generate_password_hash

app = Flask(__name__)

register_bp = Blueprint("user", __name__, url_prefix="/user")



@register_bp.route("/signup", methods=["POST"])
def signup():
    try:
        username = request.form["name"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        password = request.form["password"]
        payment_method = request.form["payment_option"]

        hashed_password = generate_password_hash(password)

        amount = 0
        expiredate = None

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Subscriber (username, email, mobile, course,password, payment_method, payment_status, amount, date, expiredate)
            VALUES (?, ?, ?,'ccc', ?, ?, ?, ?, GETDATE(), ?)
            """,
            (username, email, mobile, hashed_password, payment_method, "Pending", amount, expiredate)
        )
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": f"Hello {username}, you are registered successfully! Payment pending."
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@register_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Subscriber WHERE email=?", (email,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({"success": True, "message": "Password reset link has been sent to your email."})
    else:
        return jsonify({"success": False, "message": "No account found with that email."}), 404


@register_bp.route("/register", methods=["POST"])
def register():
    fullname = request.form["name"]
    username = request.form["email"]
    mobile = request.form["mobile"]
    course = request.form["course"]
    message = request.form.get("message", "")

    # For now, mark payment as Pending
    amount = 0  # you can map course → fee later
    expiredate = None  # will set after payment success

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Subscriber (fullname, username, mobile, course, message, payment_status, amount, date, expiredate)
        VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), ?)
    """,
        fullname,
        username,
        mobile,
        course,
        message,
        "Pending",
        amount,
        expiredate,
    )
    conn.commit()
    conn.close()

    return (
        f"Hello {fullname}, you are registered successfully! Payment pending."
    )


@register_bp.route("/exam-login", methods=["POST"])
def exam_login():
    email = request.form["email"]
    course = request.form["course"]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM Subscriber WHERE username=? AND course=?",
        (email, course),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"success": True}
    else:
        return {
            "success": False,
            "error": "No registered user for this course. Please register first.",
        }
