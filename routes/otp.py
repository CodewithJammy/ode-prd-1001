# otp.py
import os, random, time, requests
from flask import Blueprint, request, session, redirect, url_for, flash
from azure.communication.email import EmailClient
otp_bp = Blueprint('otp', __name__, url_prefix='/otp')

connection_string = os.getenv("AZURE_COMMUNICATION_CONNECTION_STRING")
email_client = EmailClient.from_connection_string(connection_string)

@otp_bp.route('/send_otp', methods=['POST'])
def send_otp():
    email = request.form.get('email')
    otp = str(random.randint(100000, 999999))

    # Save OTP + timestamp
    session['otp'] = otp
    session['otp_time'] = time.time()
    session['email'] = email

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

    if not stored_otp or not otp_time:
        flash("No OTP found, please request again.")
        return redirect(url_for('user.signup'))

    if time.time() - otp_time > 600:  # 10 minutes expiry
        flash("OTP expired, please request a new one.")
        return redirect(url_for('user.signup'))

    if entered_otp == stored_otp:
        flash("Verification successful!")
        # TODO: update user DB status here
        return redirect(url_for('user.login'))
    else:
        flash("Invalid OTP, try again.")
        return redirect(url_for('user.signup'))
