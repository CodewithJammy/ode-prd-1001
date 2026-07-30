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

    # Fast2SMS OTP API
    url = "https://www.fast2sms.com/dev/otp/send"
    payload = {
        "authorization": FAST2SMS_API_KEY,
        "variables_values": otp,
        "route": "otp",
        "numbers": mobile
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        flash("OTP sent successfully!")
    else:
        flash("Failed to send OTP. Please try again.")

    return redirect(url_for('signup'))



@otp_bp.route('/verify', methods=['POST'])
def verify_otp():
    entered_otp = request.form.get('otpCode')
    mobile = session.get('mobile')

    url = "https://www.fast2sms.com/dev/otp/verify"
    payload = {
        "authorization": FAST2SMS_API_KEY,
        "otp": entered_otp,
        "numbers": mobile
    }
    headers = {"accept": "application/json", "content-type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200 and "true" in response.text.lower():
        flash("Signup successful!")
        return redirect(url_for('home'))
    else:
        flash("Invalid or expired OTP.")
        return redirect(url_for('signup'))
