from flask import Flask,  Response, render_template, redirect

import os
from flask_cors import CORS
from routes.exam_routes  import exam_bp
from models.db_config import get_connection
from routes.admin_routes import admin_bp
from routes.register_routes import register_bp
# Create Flask app once
app = Flask(__name__)
CORS(app)  # adds CORS headers automatically

# Initialize DB
# init_db(app)


app.secret_key = os.getenv("FLASK_SECRET_KEY")


# Register the admin blueprint
app.register_blueprint(admin_bp)
app.register_blueprint(exam_bp)
app.register_blueprint(register_bp)
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/courses")
def courses():
    return render_template("exam_dashboard.html")
# Google Apps Script Web App URL
GAS_URL = "https://script.google.com/macros/s/AKfycbwbJedA3rIluoThDP3r17JbrotsKpEWqBCppgGhikuSQn1PCydVO_rMj3G0tI65I6NJLw/exec"

@app.route("/proxy", methods=["GET", "POST", "OPTIONS"])
def proxy():
    if request.method == "OPTIONS":
        # Explicit preflight response
        resp = Response()
        resp.status_code = 200
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    if request.method == "GET":
        r = requests.get(GAS_URL, params=request.args)
    else:
        r = requests.post(GAS_URL, json=request.json)

    resp = Response(r.content, status=r.status_code, content_type=r.headers.get("Content-Type"))
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

@app.route("/ping", methods=["POST"])
def ping():
    return "POST works!"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Ensures ExamQuestions table exists
    app.run(debug=True)
