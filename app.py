from flask import Flask,  Response, render_template, redirect ,request, session
import logging
import os
from flask_cors import CORS
from routes.exam_routes  import exam_bp
from models.db_config import get_connection
from routes.admin_routes import admin_bp
from routes.register_routes import register_bp
from flask_mail import Mail, Message
from routes.otp import otp_bp
from routes.user import user_bp
from routes.courses import courses_bp
from routes.tests import tests_bp
from routes.buy_item import buyitem_bp
from routes.admin import admin_bp

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.register_blueprint(otp_bp)
app.register_blueprint(user_bp)
app.register_blueprint(courses_bp)
app.register_blueprint(tests_bp)
app.register_blueprint(buyitem_bp)
app.register_blueprint(admin_bp)

@app.route('/')
def index():
    user_id = session.get('user_id')
    return render_template('index.html', is_logged_in=bool(user_id))
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
