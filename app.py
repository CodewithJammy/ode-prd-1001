from flask import Flask,  Response, render_template, redirect ,request, session
import logging
import os
from flask_cors import CORS
from flask_mail import Mail, Message
from routes.upload import upload_bp
from routes.demo_test import demotest_bp


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.register_blueprint(upload_bp)
app.register_blueprint(demotest_bp)

@app.route('/')
def index():
    user_id = session.get('user_id')
    return render_template('index.html', is_logged_in=bool(user_id))
@app.route('/search', methods=['GET', 'POST'])


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Ensures ExamQuestions table exists
    app.run(debug=True)
