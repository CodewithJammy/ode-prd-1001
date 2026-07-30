# otp.py
import os, random, time, requests
from flask import Blueprint, request, session, redirect, url_for, flash

otp_bp = Blueprint('otp', __name__, url_prefix='/otp')

FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY")  # set in environment

@otp_bp.route('/send', methods=['POST'])
def send_otp():
    mobile = request.form.get('mobileNumber')
    otp = str(random.randint(1000, 9999))

    # Store OTP + timestamp
    session['otp'] = otp
    session['otp_time'] = time.time()
    session['mobile'] = mobile

    # Fast2SMS API call
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "sender_id": "FSTSMS",  # default sender ID, DLT required for custom
        "message": f"Welcome to OneDayExam! Your OTP is {otp}",
        "language": "english",
        "route": "q",  # quick transactional route
        "numbers": mobile
    }
    headers = {
        "authorization": FAST2SMS_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(url, data=payload, headers=headers)
    if response.status_code == 200:
        flash("OTP sent successfully!")
    else:
        flash("Failed to send OTP. Please try again.")

    return redirect(url_for('signup'))

@otp_bp.route('/verify', methods=['POST'])
def verify_otp():
    entered_otp = request.form.get('otpCode')
    stored_otp = session.get('otp')
    otp_time = session.get('otp_time')

    if not stored_otp or not otp_time:
        flash("No OTP found, please request again.")
        return redirect(url_for('signup'))

    if time.time() - otp_time > 600:  # 10 minutes validity
        flash("OTP expired, please request a new one.")
        return redirect(url_for('signup'))

    if entered_otp == stored_otp:
        flash("Signup successful!")
        # TODO: Save user to DB here
        return redirect(url_for('home'))
    else:
        flash("Invalid OTP, try again.")
        return redirect(url_for('signup'))
