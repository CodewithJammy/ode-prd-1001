
from flask import Blueprint, render_template, request, session, redirect, url_for,jsonify
from models.db_config import get_connection

# Create blueprint
user_bp = Blueprint("user", __name__, url_prefix="/exam")
@user_bp.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    cursor.execute("SELECT Id FROM Users WHERE Email = ?", (email,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO Users (Email, NewUser) VALUES (?, 1)", (email,))
        conn.commit()
        user_id = cursor.execute("SELECT SCOPE_IDENTITY()").fetchval()
    else:
        user_id = row[0]
    session['user_id'] = user_id
    return redirect(url_for('user_home'))

@user_bp.route('/user-home', methods=['GET', 'POST'])
def user_home():
    cursor.execute("SELECT * FROM Users WHERE Id = ?", (session['user_id'],))
    user = cursor.fetchone()
    if user.NewUser:  # first-time profile update
        if request.method == 'POST':
            username = request.form['username']
            password = generate_password_hash(request.form['password'])
            mobile = request.form['mobile']
            gender = request.form['gender']
            cursor.execute("""
                UPDATE Users 
                SET Username=?, PasswordHash=?, Mobile=?, Gender=?, NewUser=0 
                WHERE Id=?
            """, (username, password, mobile, gender, session['user_id']))
            conn.commit()
            return redirect(url_for('user_home'))
        return render_template('profile_update.html', user=user)
    else:
        # Normal dashboard
        # Fetch orders for this user
        cursor.execute("SELECT * FROM Orders WHERE UserId=?", (session['user_id'],))
        orders = cursor.fetchall()
        return render_template('user_dashboard.html', user=user, orders=orders)
