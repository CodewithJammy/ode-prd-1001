
from flask import Blueprint, render_template, request, session, redirect, url_for,jsonify,flash
from models.db_config import get_connection
from werkzeug.security import generate_password_hash,check_password_hash
from models.db_helpers import row_to_dict


# Create connection + cursor
conn = get_connection()
cursor = conn.cursor()

# Create blueprint
user_bp = Blueprint("user", __name__, url_prefix="/user")

@user_bp.route('/user_dash', methods=['GET'])
def user_dashboard():
    return render_template('user_home.html')
    
@user_bp.route('/signup', methods=['GET'])
def signup_form():
    # Pass along "next" so we know where to go after signup
    next_url = request.args.get('next')
    return render_template('signup.html', next=next_url)


@user_bp.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    next_url = request.form.get('next')  # capture hidden field

    cursor.execute("SELECT Id FROM Users WHERE Email = ?", (email,))
    row = cursor.fetchone()

    if row:
        flash("User already exists, please login." , "warning")
        return redirect(url_for('user.login_form'))
    else:
        # Send OTP (your existing otp.send_otp logic)
        session['pending_email'] = email
        session['next_url'] = next_url  # store next in session
        return redirect(url_for('otp.send_otp'))

  
@user_bp.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    # Query user from DB
    cursor.execute("SELECT Id, PasswordHash FROM Users WHERE Email=?", (email,))
    row = cursor.fetchone()

    if row:
        user_id, stored_hash = row
        # Verify password
        if check_password_hash(stored_hash, password):
            session['user_id'] = user_id
            flash("Login successful!", "success")
            next_url = request.form.get('next') or request.args.get('next')
            if next_url and next_url != "None":
                return redirect(next_url)
            return redirect(url_for('user.user_home'))

        else:
            flash("Invalid password", "danger")
    else:
        flash("Email not found", "danger")

    return redirect(url_for('user.signup_form'))

@user_bp.route('/logout')
def logout():
    # Clear the session
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))


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
    next_url = request.args.get('next') or session.get('next_url')
    

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
            return redirect(url_for('user.user_dashboard'))
        return render_template('UserProfileUpdate.html', user=user , next=next_url)
    # Existing user   
    return  render_template('user_home.html', user=user)

@user_bp.route('/user-details')
def user_details():
    tab = request.args.get('tab', 'orders')  # default orders
    user_id = session.get('user_id')

    # fetch user once
    cursor.execute("SELECT * FROM Users WHERE Id=?", (user_id,))
    user = row_to_dict(cursor, cursor.fetchone())

    if tab == "orders":
        cursor.execute("SELECT * FROM vw_user_order WHERE UserId=?", (user_id,))
        orders = [row_to_dict(cursor, r) for r in cursor.fetchall()]
        return render_template('user_home.html', active_tab="orders",user=user , orders=orders)
    elif tab == "performance":
        cursor.execute("SELECT * FROM Performance WHERE UserId=?", (user_id,))
        perf = [row_to_dict(cursor, r) for r in cursor.fetchall()]
        return render_template('user_home.html', active_tab="performance",,user=user, performance=perf)
    elif tab == "details":
        cursor.execute("SELECT * FROM Users WHERE Id=?", (user_id,))
        user = row_to_dict(cursor, cursor.fetchone())
        return render_template('user_home.html', active_tab=tab, user=user)

