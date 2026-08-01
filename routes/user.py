
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

@user_bp.route('/user_dash', methods=['GET'])
def user_dashboard():
    return render_template('user_home.html')


def row_to_dict(cursor, row):
    """Convert a pyodbc row tuple into a dictionary keyed by column names."""
    if not row:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))

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
   
    user_id = session.get('user_id')
    print("DEBUG: session['user_id'] =", user_id)
    if not user_id:
        flash("No user session found, please login.")
        return redirect(url_for('user.signup_form'))

    cursor.execute("SELECT * FROM Users WHERE Id = ?", (user_id,))
    row = cursor.fetchone()
    user = row_to_dict(cursor, row)

    if not user:
        flash("User not found in database.")
        return redirect(url_for('user.signup_form'))

    

    if int(user["NewUser"]) == 1:
        # First-time profile update
        if request.method == 'POST':
            username = request.form['username']
            password = generate_password_hash(request.form['password'])
            mobile = request.form['mobile']
            gender = request.form['gender']
            cursor.execute("""
                UPDATE Users 
                SET Username=?, PasswordHash=?, Mobile=?, Gender=?, NewUser=0 
                WHERE Id=?
            """, (username, password, mobile, gender, user_id))
            conn.commit()
            return redirect(url_for('user.user_dash'))
        return render_template('UserProfileUpdate.html', user=user)
    # Existing user   
    return redirect(url_for('user.user_dash'))
