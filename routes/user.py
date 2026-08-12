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


# ============================================================
# BLUEPRINT
# ============================================================

user_bp = Blueprint(
    "user",
    __name__,
    url_prefix="/user"
)


# ============================================================
# USER PROFILE
# ============================================================

@user_bp.route(
    "/profile",
    methods=["GET", "POST"]
)
def profile():

    # --------------------------------------------------------
    # Get Google ID from session
    # --------------------------------------------------------

    google_id = session.get("google_id")

    if not google_id:

        return redirect(
            url_for("auth.login")
        )

    # --------------------------------------------------------
    # Get Users sheet
    # --------------------------------------------------------

    sheet = get_worksheet("Users")

    records = sheet.get_all_records()

    # --------------------------------------------------------
    # Find current user
    # --------------------------------------------------------

    user = None

    for row in records:

        if (
            str(row.get("GoogleId", "")).strip()
            ==
            str(google_id).strip()
        ):

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

        # ----------------------------------------------------
        # Update failed
        # ----------------------------------------------------

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

        session["google_id"] = google_id

        session["user_id"] = updated_user.get(
            "UserId"
        )

        # ----------------------------------------------------
        # Profile completed
        # ----------------------------------------------------

        return redirect(
            url_for("user.user_home")
        )

    # ========================================================
    # GET - SHOW PROFILE
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

    google_id = session.get("google_id")

    if not google_id:

        return redirect(
            url_for("auth.login")
        )

    # --------------------------------------------------------
    # Get Users sheet
    # --------------------------------------------------------

    sheet = get_worksheet("Users")

    records = sheet.get_all_records()

    # --------------------------------------------------------
    # Find current user
    # --------------------------------------------------------

    user = None

    for row in records:

        if (
            str(row.get("GoogleId", "")).strip()
            ==
            str(google_id).strip()
        ):

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
    # New user
    #
    # User has not completed profile yet.
    # --------------------------------------------------------

    if str(
        user.get("NewUser", "")
    ).strip() == "1":

        return redirect(
            url_for("user.profile")
        )

    # ========================================================
    # TEMPORARY
    #
    # You don't have user_home.html yet.
    # So use profile.html for now.
    # ========================================================

    return render_template(
        "profile.html",
        user=user
    )
