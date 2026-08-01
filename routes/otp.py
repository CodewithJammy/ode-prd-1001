import os, random, time
from flask import Blueprint, request, session, redirect, url_for, flash
from azure.communication.email import EmailClient
from models.db_config import get_connection

otp_bp = Blueprint('otp', __name__, url_prefix='/otp')

connection_string = os.getenv("AZURE_COMMUNICATION_CONNECTION_STRING")
email_client = EmailClient.from_connection_string(connection_string)

conn = get_connection()
cursor = conn.cursor()

@otp_bp.route('/send_otp', methods=['POST'])
def send_otp():
    email = request.form.get('email')

    # Check if email already exists
    cursor.execute("SELECT Id FROM Users WHERE Email = ?", (email,))
    row = cursor.fetchone()

    if row:
        flash("User already exists, please login.")
        return redirect(url_for('user.signup'))
    else:
        otp = str(random.randint(100000, 999999))
        session['otp'] = otp
        session['otp_time'] = time.time()
        session['pending_email'] = email

        message = {
            "senderAddress": "DoNotReply@8eba1789-8297-4341-a70c-f23f248cd46b.azurecomm.net",
            "recipients": {"to": [{"address": email}]},
            "content": {
                "subject": "Your OneDayExam OTP",
                "plainText": f"Your OTP is {otp}. It will expire in 10 minutes."
            }
        }

        poller = email_client.begin_send(message)
        result = poller.result()
        print("Email send status:", result)

        flash("OTP sent to your email!")
        return redirect(url_for('user.signup'))

@otp_bp.route('/verify_otp', methods=['POST'])
def verify_otp():
    entered_otp = request.form.get('otpCode')
    stored_otp = session.get('otp')
    otp_time = session.get('otp_time')
    email = session.get('pending_email')

    print("DEBUG: Incoming verify_otp request")
    print("DEBUG: entered_otp =", entered_otp)
    print("DEBUG: stored_otp =", stored_otp)
    print("DEBUG: pending_email =", email)
    print("DEBUG: session contents BEFORE insert =", dict(session))
    
    if not stored_otp or not otp_time:
        flash("No OTP found, please request again.")
        return redirect(url_for('user.signup'))

    if time.time() - otp_time > 600:
        flash("OTP expired, please request a new one.")
        return redirect(url_for('user.signup'))

    if entered_otp == stored_otp:
        cursor.execute("INSERT INTO Users (Email, NewUser) VALUES (?, 1)", (email,))
        conn.commit()
        
        cursor.execute("SELECT Id, NewUser FROM Users WHERE Email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            print("DEBUG: No row found for email =", email)
            flash("User creation failed, please try again.")
            return redirect(url_for('user.signup'))
            
        user_id, new_user_flag = row  # unpack both values

        session['user_id'] = user_id   # Store in session
        print("DEBUG: session contents AFTER insert =", dict(session))
        
        flash("Verification successful! Please complete your profile.")
        
        #  Use new_user_flag directly
        return redirect(url_for('user.user_home', newUser=str(new_user_flag) ,userId=user_id))
    else:
        flash("Invalid OTP, try again.")
        return redirect(url_for('user.signup'))
