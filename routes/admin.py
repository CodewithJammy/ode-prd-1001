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
    cursor.execute("SELECT Id, Name FROM Courses")
    courses = cursor.fetchall()

    # Fetch tests
    cursor.execute("SELECT Id, Name FROM Tests")
    tests = cursor.fetchall()

    # Fetch topics
    cursor.execute("SELECT Id, Title FROM Topics")
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
    desc = request.form['description']
    cursor.execute("INSERT INTO Courses (Name, Description) VALUES (?, ?)", (name, desc))
    conn.commit()
    flash("Course added successfully!", "success")
    return redirect(url_for('admin.dashboard'))


# Add Test
@admin_bp.route('/add-test', methods=['POST'])
def add_test():
    course_id = request.form['course_id']
    name = request.form['name']
    test_type = request.form['test_type']
    year = request.form.get('year')
    cursor.execute("INSERT INTO Tests (CourseId, Name, Test_Type, Year) VALUES (?, ?, ?, ?)",
                   (course_id, name, test_type, year))
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
