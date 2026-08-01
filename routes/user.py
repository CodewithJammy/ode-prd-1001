
from flask import Blueprint, render_template, request, session, redirect, url_for,jsonify,flash
from models.db_config import get_connection
from werkzeug.security import generate_password_hash


# Create connection + cursor
conn = get_connection()
cursor = conn.cursor()

# Create blueprint
user_bp = Blueprint("user", __name__, url_prefix="/user")

@user_bp.route('/signup', methods=['GET'])
def signup_form():
    return render_template('signup.html')


@user_bp.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    cursor.execute("SELECT Id FROM Users WHERE Email = ?", (email,))
    row = cursor.fetchone()

    if row:
        flash("User already exists, please login.")
        return redirect(url_for('user.login_form'))
    else:
        # Send OTP (your existing otp.send_otp logic)
        session['pending_email'] = email
        return redirect(url_for('otp.send_otp'))
  

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
        return render_template('UserProfileUpdate.html', user=user)
    else:
        # Normal dashboard
        # Fetch orders for this user
        cursor.execute("SELECT * FROM Orders WHERE UserId=?", (session['user_id'],))
        orders = cursor.fetchall()
        return render_template('user_home.html', user=user, orders=orders)
