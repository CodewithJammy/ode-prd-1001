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
    # Query Questions table for this test and topic
    query = "SELECT * FROM Questions WHERE TestId=? AND TopicId=?"
    cursor.execute(query, (test_id, topic_id))
    rows = cursor.fetchall()
    questions = [row_to_dict(cursor, r) for r in rows]

    return render_template('topic_testpage.html', questions=questions)


@admin_bp.route('/upload-questions', methods=['POST'])
def upload_questions():
    course_id = request.form['course_id']
    test_id = request.form['test_id']
    topic_id = request.form['topic_id']
    file = request.files['questions_file']

    errors = []
    df = None

    if file.filename.endswith('.csv'):
        df = pd.read_csv(file)
    elif file.filename.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file)
    else:
        flash("Unsupported file type", "danger")
        return redirect(url_for('admin.dashboard'))

    for i, row in df.iterrows():
        if str(row['CourseId']) != course_id:
            errors.append(f"Row {i+2}: CourseId mismatch")
        if str(row['TestId']) != test_id:
            errors.append(f"Row {i+2}: TestId mismatch")
        if str(row['TopicId']) != topic_id:
            errors.append(f"Row {i+2}: TopicId mismatch")

    if errors:
        for e in errors:
            flash(e, "danger")
        flash("Validation failed. Fix file before upload.", "danger")
        return redirect(url_for('admin.dashboard'))

    # If validation passes, insert into Questions table
    for i, row in df.iterrows():
        cursor.execute("""
            INSERT INTO Questions (TestId, TopicId, QuestionText, OptionA, OptionB, OptionC, OptionD, CorrectAnswer)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (test_id, topic_id, row['QuestionText'], row['OptionA'], row['OptionB'], row['OptionC'], row['OptionD'], row['CorrectAnswer']))
    conn.commit()

    flash("Questions uploaded successfully!", "success")
    return redirect(url_for('admin.dashboard'))



