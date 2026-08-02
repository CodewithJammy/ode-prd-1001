from flask import Blueprint, render_template, request
from models.db_config import get_connection
from models.db_helpers import row_to_dict

# Create connection + cursor
conn = get_connection()
cursor = conn.cursor()

# Create blueprint
tests_bp = Blueprint("tests", __name__, url_prefix="/tests")

@tests_bp.route('/tests')
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

    return render_template('tests.html', tests=tests, categories=categories, levels=levels)
