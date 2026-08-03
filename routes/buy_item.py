import os, random, time
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, session, redirect, url_for,jsonify,flash
from models.db_config import get_connection
from werkzeug.security import generate_password_hash,check_password_hash
from models.db_helpers import row_to_dict




# Create connection + cursor
conn = get_connection()
cursor = conn.cursor()
buyitem_bp = Blueprint("buy", __name__, url_prefix="/buy")

@buyitem_bp.route('/buy/<item_type>/<int:item_id>')
def buy_item(item_type, item_id):
    if not session.get('user_id'):
        # Not logged in → redirect to signup with "next"
        return redirect(url_for('signup', next=url_for('buy.buy_item', item_type=item_type, item_id=item_id)))
    else:
        # Logged in → go straight to payment
        return redirect(url_for('buy.payment', item_type=item_type, item_id=item_id))




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
    order_type = request.form['order_type']
    order_typeid = request.form['order_typeid']
    price = request.form.get('price')
    method = request.form.get('method', 'cash')

    start_date = datetime.now()
    expire_date = start_date + timedelta(days=90)  # 3 months

    cursor.execute("""
        INSERT INTO Orders (UserId,  order_type, order_typeid,amount ,PaymentMethod, orderdate, order_expiredate)
        VALUES (?, ?, ?, ?, ?, ?, ? )
    """, (user_id, order_type, order_typeid, price , method, start_date, expire_date))
    conn.commit()

    flash("Payment successful! Your course/test has been activated.")
    return redirect(url_for('user.user_dashboard'))

