
import os
import logging
from flask_cors import CORS
from flask_mail import Mail, Message
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask,  Response, render_template, redirect ,request, session

from routes.auth import auth_bp
from routes.user import user_bp
from routes.upload import upload_bp
from routes.demo_test import demotest_bp




app = Flask(__name__)

app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_proto=1,
    x_host=1
)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.register_blueprint(upload_bp)
app.register_blueprint(demotest_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)

@app.route("/")
def home():
    return render_template("home.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Ensures ExamQuestions table exists
    app.run(debug=True)
