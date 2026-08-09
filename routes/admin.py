from flask import Blueprint, render_template, request, redirect, url_for, flash ,jsonify
import pyodbc
from models.db_config import get_connection
import pandas as pd

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Database connection (adjust for your SQL Server)
conn = get_connection()
cursor = conn.cursor()

# Admin dashboard route
@admin_bp.route('/dashboard', methods=['GET'])
def dashboard():
    # Fetch courses
    cursor.execute("SELECT * FROM Courses")
    courses = cursor.fetchall()

    # Fetch tests
    cursor.execute("SELECT * FROM Tests")
    tests = cursor.fetchall()

    # Fetch topics
    cursor.execute("SELECT * FROM Topics")
    topics = cursor.fetchall()

    return render_template(
        'admin.html',
        courses=courses,
        tests=tests,
        topics=topics
    )

# Add Course
@admin_bp.route('/add-course', methods=['POST'])
def add_course():
    name = request.form['name']
    desc = request.form.get('description')
    image_url = request.form.get('image_url')
    price = request.form.get('price')
    category = request.form.get('category')
    duration = request.form.get('duration')
    level = request.form.get('level')
    syllabus_pdf_url = request.form.get('syllabus_pdf_url')

    cursor.execute("""
        INSERT INTO Courses (Name, Description, ImageUrl, Price, Category, Duration, Level, SyllabusPdfUrl)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, desc, image_url, price, category, duration, level, syllabus_pdf_url))
    conn.commit()
    flash("Course added successfully!", "success")
    return redirect(url_for('admin.dashboard'))

# Add Test
@admin_bp.route('/add-test', methods=['POST'])
def add_test():
    course_id = request.form['course_id']
    name = request.form['name']
    price = request.form.get('price')
    test_type = request.form['test_type']
    year = request.form.get('year')

    cursor.execute("""
        INSERT INTO Tests (CourseId, Name, Price, Test_Type)
        VALUES (?, ?, ?, ?)
    """, (course_id, name, price, test_type))
    conn.commit()
    flash("Test added successfully!", "success")
    return redirect(url_for('admin.dashboard'))

# Add Topic
@admin_bp.route('/add-topic', methods=['POST'])
def add_topic():
    course_id = request.form['course_id']
    test_id = request.form['test_id']
    topic_names = request.form.getlist('topic_name[]')

    for topic_name in topic_names:
        # Increment OrderNo per course+test
        cursor.execute("SELECT ISNULL(MAX(OrderNo), 0) FROM Topics WHERE CourseId = ? AND TestId = ?", (course_id, test_id))
        max_order_no = cursor.fetchone()[0]
        new_order_no = max_order_no + 1

        cursor.execute(
            "INSERT INTO Topics (CourseId, TestId, Title, OrderNo) VALUES (?, ?, ?, ?)",
            (course_id, test_id, topic_name, new_order_no)
        )

    conn.commit()
    flash(f"{len(topic_names)} topic(s) added successfully with order numbers!", "success")
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/get-courses', methods=['GET'])
def get_courses():
    cursor.execute("SELECT Id, Name, Price FROM Courses")
    courses = cursor.fetchall()
    return jsonify([
        {"id": c.Id, "name": c.Name, "price": c.Price}
        for c in courses
    ])


@admin_bp.route('/get-tests/<int:course_id>', methods=['GET'])
def get_tests(course_id):
    cursor.execute("SELECT Id, Name FROM Tests WHERE courseid = ?", (course_id,))
    tests = cursor.fetchall()
    return jsonify([{"id": t.Id, "name": t.Name} for t in tests])

@admin_bp.route('/get-topics/<int:test_id>', methods=['GET'])
def get_topics(test_id):
    cursor.execute("SELECT Id, Title, TestId, CourseId FROM Topics WHERE TestId = ?", (test_id,))
    topics = cursor.fetchall()
    return jsonify([
        {"id": t.Id, "title": t.Title, "testId": t.TestId, "courseId": t.CourseId}
        for t in topics
    ])





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






@admin_bp.route('/validate-questions', methods=['POST'])
def validate_questions():
    course_id = request.form['course_id']
    test_id = request.form['test_id']
    topic_id = request.form['topic_id']
    file = request.files['questions_file']

    # Read file
    if file.filename.endswith('.csv'):
        df = pd.read_csv(file)
    elif file.filename.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file)
    else:
        flash("Unsupported file type", "danger")
        return redirect(url_for('admin.dashboard'))

    # Add validation flag
    df['ValidFlag'] = df.apply(
        lambda row: int(
            str(row['CourseId']) == str(course_id) and
            str(row['TestId']) == str(test_id) and
            str(row['TopicId']) == str(topic_id)
        ),
        axis=1
    )

    # Preview first 10 rows
    preview = df.head(10).to_dict(orient='records')

    # Check if all rows valid
    all_valid = df['ValidFlag'].all()

    return render_template(
        'preview_questions.html',
        all_valid=all_valid,
        course_id=course_id,
        test_id=test_id,
        topic_id=topic_id,
        file=file.filename
    )





