# otp.py
import os, random, time
from flask import Blueprint, request, session, redirect, url_for, flash
from twilio.rest import Client

otp_bp = Blueprint('otp', __name__, url_prefix='/otp')

# Load credentials
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
api_key = os.getenv("TWILIO_API_KEY")
api_secret = os.getenv("TWILIO_API_SECRET")
messaging_service_sid = os.getenv("TWILIO_MESSAGING_SERVICE_SID")

client = Client(api_key, api_secret, account_sid)

@otp_bp.route('/send', methods=['POST'])
def send_otp():
    mobile = request.form.get('mobileNumber')
    otp = str(random.randint(1000, 9999))

    # Store OTP + timestamp in session
    session['otp'] = otp
    session['otp_time'] = time.time()
    session['mobile'] = mobile

    # Send SMS via Messaging Service (no number shown)
    client.messages.create(
        messaging_service_sid=messaging_service_sid,
        body=f"Welcome to OneDayExam! Your OTP is {otp}",
        to=f"+91{mobile}"
    )

    flash("OTP sent to your mobile number!")
    return redirect(url_for('signup'))

@otp_bp.route('/verify', methods=['POST'])
def verify_otp():
    entered_otp = request.form.get('otpCode')
    stored_otp = session.get('otp')
    otp_time = session.get('otp_time')

    # Check validity (10 minutes = 600 seconds)
    if not stored_otp or not otp_time:
        flash("No OTP found, please request again.")
        return redirect(url_for('signup'))

    if time.time() - otp_time > 600:
        flash("OTP expired, please request a new one.")
        return redirect(url_for('signup'))

    if entered_otp == stored_otp:
        flash("Signup successful!")
        # TODO: Save user to DB here
        return redirect(url_for('home'))
    else:
        flash("Invalid OTP, try again.")
        return redirect(url_for('signup'))
