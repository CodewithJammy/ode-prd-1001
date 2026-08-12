from flask import (
    Blueprint,
    session,
    render_template,
    redirect,
    request,
    url_for
)

from services.sheet_service import get_worksheet

from services.user_service import (
    update_user_profile
)


user_bp = Blueprint(
    "user",
    __name__,
    url_prefix="/user"
)


# ============================================================
# USER PROFILE / USER HOME
# ============================================================

@user_bp.route(
    "/profile",
    methods=["GET", "POST"]
)
def profile():

    # --------------------------------------------------------
    # Get Google ID from session
    # --------------------------------------------------------

    google_id = session.get(
        "google_id"
    )

    if not google_id:

        return redirect(
            url_for("auth.login")
        )

    # --------------------------------------------------------
    # Get Users sheet
    # --------------------------------------------------------

    sheet = get_worksheet(
        "Users"
    )

    records = sheet.get_all_records()

    # --------------------------------------------------------
    # Find current user
    # --------------------------------------------------------

    user = None

    for row in records:

        if str(
            row.get("GoogleId")
        ) == str(google_id):

            user = row

            break

    # --------------------------------------------------------
    # User not found
    # --------------------------------------------------------

    if not user:

        session.clear()

        return redirect(
            url_for("auth.login")
        )

    # ========================================================
    # POST - SAVE PROFILE
    # ========================================================

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        gender = request.form.get(
            "gender",
            ""
        ).strip()

        # ----------------------------------------------------
        # Basic validation
        # ----------------------------------------------------

        if not username:

            return render_template(
                "profile.html",
                user=user,
                error="Please enter your username."
            )

        # ----------------------------------------------------
        # Update Google Sheet
        # ----------------------------------------------------

        updated_user = update_user_profile(
            google_id=google_id,
            username=username,
            mobile=mobile,
            gender=gender
        )

        if not updated_user:

            return render_template(
                "profile.html",
                user=user,
                error=(
                    "Unable to update your profile. "
                    "Please try again."
                )
            )

        # ----------------------------------------------------
        # Update Flask session
        # ----------------------------------------------------

        session["user"] = updated_user

        # ----------------------------------------------------
        # Profile completed
        # ----------------------------------------------------

        return redirect(
            url_for("user.user_home")
        )

    # ========================================================
    # GET
    # ========================================================

    return render_template(
        "profile.html",
        user=user
    )


# ============================================================
# USER HOME
# ============================================================

@user_bp.route(
    "/user-home"
)
def user_home():

    # --------------------------------------------------------
    # Get Google ID
    # --------------------------------------------------------

    google_id = session.get(
        "google_id"
    )

    if not google_id:

        return redirect(
            url_for("auth.login")
        )

    # --------------------------------------------------------
    # Get user from Sheet
    # --------------------------------------------------------

    sheet = get_worksheet(
        "Users"
    )

    records = sheet.get_all_records()

    user = None

    for row in records:

        if str(
            row.get("GoogleId")
        ) == str(google_id):

            user = row

            break

    # --------------------------------------------------------
    # User not found
    # --------------------------------------------------------

    if not user:

        session.clear()

        return redirect(
            url_for("auth.login")
        )

    # --------------------------------------------------------
    # Still a new user
    #
    # Send them back to profile completion.
    # --------------------------------------------------------

    if str(
        user.get("NewUser")
    ) == "1":

        return redirect(
            url_for("user.profile")
        )

    # --------------------------------------------------------
    # Normal user home
    # --------------------------------------------------------

    return render_template(
        "user_home.html",
        user=user
    )
