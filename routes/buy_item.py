buyitem_bp = Blueprint("buy", __name__, url_prefix="/buy")

@buyitem_bp.route('/buy/<item_type>/<int:item_id>')
def buy_item(item_type, item_id):
    if not session.get('user_id'):
        # Not logged in → redirect to signup with "next"
        return redirect(url_for('signup', next=url_for('buy_item', item_type=item_type, item_id=item_id)))
    else:
        # Logged in → go straight to payment
        return redirect(url_for('payment', item_type=item_type, item_id=item_id))
