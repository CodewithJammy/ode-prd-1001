from flask import Blueprint, render_template, request, redirect, url_for, flash
import pyodbc
from models.db_config import get_connection

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
        INSERT INTO Tests (CourseId, Name, Price, Test_Type, Year)
        VALUES (?, ?, ?, ?, ?)
    """, (course_id, name, price, test_type, year))
    conn.commit()
    flash("Test added successfully!", "success")
    return redirect(url_for('admin.dashboard'))

# Add Topic
@admin_bp.route('/add-topic', methods=['POST'])
def add_topic():
    test_id = request.form['test_id']
    topic_name = request.form['topic_name']

    cursor.execute("INSERT INTO Topics (TestId, Title) VALUES (?, ?)", (test_id, topic_name))
    conn.commit()
    flash("Topic added successfully!", "success")
    return redirect(url_for('admin.dashboard'))
