from flask import Flask,  Response, render_template, redirect ,request
import logging
import os
from flask_cors import CORS
from routes.exam_routes  import exam_bp
from models.db_config import get_connection
from routes.admin_routes import admin_bp
from routes.register_routes import register_bp
from flask_mail import Mail, Message
from routes.otp import otp_bp

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.register_blueprint(otp_bp)

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/signup')
def signup():
    return render_template('signup.html')    
@app.route('/courses')
def courses():
    return render_template('courses.html')
@app.route('/tests')
def tests():
    return render_template('tests.html')
@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.args.get('q')  # get search term from URL
    # For now, just show the query back
    # Later you can filter courses/tests from a database
    return render_template('search_results.html', query=query)


@app.route("/ping", methods=["POST"])
def ping():
    return "POST works!"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Ensures ExamQuestions table exists
    app.run(debug=True)
