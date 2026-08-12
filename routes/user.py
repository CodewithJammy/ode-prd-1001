from flask import Blueprint, session, render_template

from services.sheet_service import get_worksheet


user_bp = Blueprint(
    "user",
    __name__,
    url_prefix="/user"
)


@user_bp.route("/user-home")
def user_home():

    google_id = session.get("google_id")

    if not google_id:
        return redirect(
            url_for("auth.login")
        )

    sheet = get_worksheet("Users")

    records = sheet.get_all_records()

    user = None

    for row in records:

        if str(row.get("GoogleId")) == str(google_id):

            user = row
            break

    if not user:
        return redirect(
            url_for("auth.login")
        )

    if str(user.get("NewUser")) == "1":

        return render_template(
            "profile.html",
            user=user
        )

    return render_template(
        "user_home.html",
        user=user
    )
