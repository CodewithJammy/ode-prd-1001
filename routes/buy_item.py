import os, random, time
from flask import Blueprint, request, session, redirect, url_for, flash
from datetime import datetime, timedelta


buyitem_bp = Blueprint("buy", __name__, url_prefix="/buy")

@buyitem_bp.route('/buy/<item_type>/<int:item_id>')
def buy_item(item_type, item_id):
    if not session.get('user_id'):
        # Not logged in → redirect to signup with "next"
        return redirect(url_for('signup', next=url_for('buy_item', item_type=item_type, item_id=item_id)))
    else:
        # Logged in → go straight to payment
        return redirect(url_for('payment', item_type=item_type, item_id=item_id))




@buyitem_bp.route('/payment/<item_type>/<int:item_id>', methods=['GET', 'POST'])
def payment(item_type, item_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Please login first.")
        return redirect(url_for('user.signup_form'))

    # Fetch user info
    cursor.execute("SELECT Id, Username, Email, Mobile FROM Users WHERE Id=?", (user_id,))
    user = row_to_dict(cursor, cursor.fetchone())

    # Fetch course/test info
    if item_type == 'course':
        cursor.execute("SELECT Id, Name, Description, Price FROM Courses WHERE Id=?", (item_id,))
    else:
        cursor.execute("SELECT Id, Name, Description, Price FROM Tests WHERE Id=?", (item_id,))
    item = row_to_dict(cursor, cursor.fetchone())

    return render_template('payment.html', item=item, item_type=item_type, user=user)


@buyitem_bp.route('/process_payment/<item_type>/<int:item_id>', methods=['POST'])
def process_payment(item_type, item_id):
    user_id = request.form['user_id']
    username = request.form['username']
    email = request.form['email']
    mobile = request.form['mobile']
    order_type = request.form['order_type']
    order_typeid = request.form['order_id']
    method = request.form['method']

    start_date = datetime.now()
    expire_date = start_date + timedelta(days=90)  # 3 months

    cursor.execute("""
        INSERT INTO Orders (UserId, Username, Email, Mobile, CourseType, CourseId, PaymentMethod, StartDate, ExpireDate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username, email, mobile, order_type, order_typeid, method, start_date, expire_date))
    conn.commit()

    flash("Payment successful! Your course/test has been activated.")
    return redirect(url_for('user.user_dashboard'))

