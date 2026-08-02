from flask import Blueprint, render_template, request, session, redirect, url_for,jsonify,flash
from models.db_config import get_connection
from werkzeug.security import generate_password_hash
from models.db_helpers import row_to_dict

# Create connection + cursor
conn = get_connection()
cursor = conn.cursor()

# Create blueprint
courses_bp = Blueprint("courses", __name__, url_prefix="/courses")
@courses_bp.route('/courses')
def courses():
    # Read filters from query string
    category = request.args.get('category')
    price = request.args.get('price')

    query = "SELECT * FROM Courses WHERE 1=1"
    params = []

    if category:
        query += " AND Category=?"
        params.append(category)
    if price == "low":
        query += " AND Price < 500"
    elif price == "mid":
        query += " AND Price BETWEEN 500 AND 1000"
    elif price == "high":
        query += " AND Price > 1000"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    courses = [row_to_dict(cursor, r) for r in rows]

    return render_template('courses.html', courses=courses)
