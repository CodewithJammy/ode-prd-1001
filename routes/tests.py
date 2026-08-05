from flask import Blueprint, render_template, request, session
from models.db_config import get_connection
from models.db_helpers import row_to_dict
from werkzeug.security import generate_password_hash

# Create connection + cursor
conn = get_connection()
cursor = conn.cursor()

# Create blueprint
tests_bp = Blueprint("tests", __name__, url_prefix="/tests")

@tests_bp.route('/')
def tests():
    # Get distinct categories
    cursor.execute("SELECT DISTINCT Category FROM Tests")
    categories = [row[0] for row in cursor.fetchall()]

    # Get distinct levels
    cursor.execute("SELECT DISTINCT Level FROM Tests")
    levels = [row[0] for row in cursor.fetchall()]

    # Apply filters
    category = request.args.get('category')
    price = request.args.get('price')
    level = request.args.get('level')

    query = "SELECT * FROM Tests WHERE 1=1"
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
    if level:
        query += " AND Level=?"
        params.append(level)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    tests = [row_to_dict(cursor, r) for r in rows]
    template = 'user_tests.html' if session.get('user_id') else 'tests.html'
    return render_template('tests.html', tests=tests, categories=categories, levels=levels)


@tests_bp.route('/test/<int:test_id>/topic/<int:topic_id>')
def topic_testpage(test_id, topic_id):
    questions = (
        db.session.query(Questions)
        .filter_by(TestId=test_id, TopicId=topic_id)
        .all()
    )
    return render_template('topic_testpage.html', questions=questions)

