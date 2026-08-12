from flask import (
    Blueprint,
    session,
    render_template,
    redirect,
    url_for
)

from services.sheet_service import get_worksheet


user_bp = Blueprint(
    "user",
    __name__,
    url_prefix="/user"
)


@user_bp.route("/profile")
def profile():

    google_id = session.get("google_id")

    # User is not logged in
    if not google_id:
        return redirect(
            url_for("auth.login")
        )

    # Get Users sheet
    sheet = get_worksheet("Users")

    # Get all users
    records = sheet.get_all_records()

    user = None

    # Find logged-in user
    for row in records:

        if str(row.get("GoogleId", "")).strip() == str(google_id).strip():

            user = row
            break

    # User not found in Sheet
    if not user:

        session.clear()

        return redirect(
            url_for("auth.login")
        )

    # Store user in session
    session["user"] = user

    # Open profile page
    return render_template(
        "profile.html",
        user=user
    )
