import pyodbc
from flask import Flask, Blueprint, render_template, request, session, redirect, url_for,jsonify,current_app
from models.db_config import get_connection
from werkzeug.security import generate_password_hash
from flask_mail import Message
import secrets
from datetime import datetime, timedelta
import logging
import smtplib



logging.basicConfig(level=logging.INFO)

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
    try:
        data = request.get_json(silent=True)
        if not data or "email" not in data:
            return jsonify({"success": False, "message": "Invalid request format"}), 400

        email = data["email"]
        logging.info("Parsed email: %s", email)

        # DB lookup logic here...

        reset_link = url_for('user.reset_password', token="dummy", _external=True)

        msg = Message("Password Reset Request", recipients=[email])
        msg.body = f"Click the link to reset your password:\n{reset_link}\n\nThis link expires in 1 hour."

        try:
            logging.info("Connecting to SMTP server %s:%s",
                         current_app.config['MAIL_SERVER'],
                         current_app.config['MAIL_PORT'])
            logging.info("TLS: %s, SSL: %s",
                         current_app.config['MAIL_USE_TLS'],
                         current_app.config['MAIL_USE_SSL'])

            # Force a manual test connection before sending
            server = smtplib.SMTP(current_app.config['MAIL_SERVER'],
                                  current_app.config['MAIL_PORT'])
            if current_app.config['MAIL_USE_TLS']:
                server.starttls()
            server.login(current_app.config['MAIL_USERNAME'],
                         current_app.config['MAIL_PASSWORD'])
            logging.info("SMTP login successful")

            # Now let Flask-Mail send
            current_app.extensions['mail'].send(msg)
            logging.info("Password reset email sent to %s", email)

        except Exception as smtp_error:
            logging.exception("SMTP send failed")
            return jsonify({"success": False, "message": f"Email send failed: {smtp_error}"}), 500

        return jsonify({"success": True, "message": "Password reset link has been sent to your email."})
    except Exception as e:
        logging.exception("Forgot password route failed")
        return jsonify({"success": False, "message": str(e)}), 400



@register_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT reset_expire FROM Subscriber WHERE reset_token=?", (token,))
        row = cursor.fetchone()

        # If no row or expired
        if not row or row[0] < datetime.utcnow():
            return "Reset link expired or invalid", 400

        if request.method == "POST":
            new_password = request.form["password"]
            hashed_password = generate_password_hash(new_password)

            cursor.execute(
                "UPDATE Subscriber SET password=?, reset_token=NULL, reset_expire=NULL WHERE reset_token=?",
                (hashed_password, token)
            )
            conn.commit()
            return "Password updated successfully!"

        # GET request → render form
        return render_template("reset_password.html", token=token)
    finally:
        conn.close()




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
