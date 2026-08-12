import os
import requests

from flask import (
    Blueprint,
    redirect,
    request,
    session,
    url_for,
    render_template
)

from google_auth_oauthlib.flow import Flow

from services.user_service import (
    find_user_by_google_id,
    create_user
)


# ============================================================
# Blueprint
# ============================================================

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


# ============================================================
# Google OAuth Configuration
# ============================================================

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

REDIRECT_URI = (
    "https://exambank.azurewebsites.net/auth/google/callback"
)


CLIENT_CONFIG = {
    "web": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,

        "auth_uri":
            "https://accounts.google.com/o/oauth2/auth",

        "token_uri":
            "https://oauth2.googleapis.com/token",

        "redirect_uris": [
            REDIRECT_URI
        ]
    }
}


# ============================================================
# Google OAuth Scopes
# ============================================================

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]


# ============================================================
# ACCOUNT
# ============================================================

@auth_bp.route("/account")
def account():

    google_id = session.get("google_id")

    # --------------------------------------------------------
    # User is NOT logged in
    # --------------------------------------------------------

    if not google_id:

        return redirect(
            url_for("auth.login")
        )

    # --------------------------------------------------------
    # User is already logged in
    # --------------------------------------------------------

    return redirect(
        url_for("user.profile")
    )


# ============================================================
# LOGIN PAGE
# ============================================================

@auth_bp.route("/login")
def login():

    return render_template(
        "login.html"
    )


# ============================================================
# START GOOGLE LOGIN
# ============================================================

@auth_bp.route("/google")
def google_login():

    # --------------------------------------------------------
    # Check Google configuration
    # --------------------------------------------------------

    if not CLIENT_ID or not CLIENT_SECRET:

        return (
            "Google OAuth is not configured correctly "
            "in Azure App Settings.",
            500
        )

    # --------------------------------------------------------
    # Create OAuth flow
    # --------------------------------------------------------

    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES
    )

    # --------------------------------------------------------
    # Callback URL
    # --------------------------------------------------------

    flow.redirect_uri = url_for(
        "auth.google_callback",
        _external=True
    )

    # --------------------------------------------------------
    # Generate Google authorization URL
    # --------------------------------------------------------

    authorization_url, state = (
        flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="select_account"
        )
    )

    # --------------------------------------------------------
    # Save OAuth state in Flask session
    # --------------------------------------------------------

    session["google_oauth_state"] = state

    # --------------------------------------------------------
    # Redirect user to Google
    # --------------------------------------------------------

    return redirect(
        authorization_url
    )


# ============================================================
# GOOGLE CALLBACK
# ============================================================

@auth_bp.route("/google/callback")
def google_callback():

    # --------------------------------------------------------
    # Get OAuth state
    # --------------------------------------------------------

    state = session.get(
        "google_oauth_state"
    )

    if not state:

        return (
            "Google login session expired. "
            "Please try again.",
            400
        )

    # --------------------------------------------------------
    # Create OAuth flow again
    # --------------------------------------------------------

    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        state=state
    )

    # --------------------------------------------------------
    # Callback URL
    # --------------------------------------------------------

    flow.redirect_uri = url_for(
        "auth.google_callback",
        _external=True
    )

    # --------------------------------------------------------
    # Exchange authorization code for token
    # --------------------------------------------------------

    flow.fetch_token(
        authorization_response=request.url
    )

    credentials = flow.credentials

    # --------------------------------------------------------
    # Get Google user information
    # --------------------------------------------------------

    response = requests.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={
            "Authorization":
                f"Bearer {credentials.token}"
        },
        timeout=10
    )

    response.raise_for_status()

    google_user = response.json()

    # --------------------------------------------------------
    # Google unique user ID
    # --------------------------------------------------------

    google_id = google_user.get("sub")

    if not google_id:

        return (
            "Google did not return a user ID.",
            400
        )

    # --------------------------------------------------------
    # Find user in Google Sheet
    # --------------------------------------------------------

    user = find_user_by_google_id(
        google_id
    )

    # --------------------------------------------------------
    # User doesn't exist
    # Create new user in Sheet
    # --------------------------------------------------------

    if not user:

        user = create_user(
            google_user
        )

    # --------------------------------------------------------
    # Store login information in Flask session
    # --------------------------------------------------------

    session["user_id"] = user["UserId"]

    session["google_id"] = google_id

    session["user"] = user

    # OAuth state is no longer required
    session.pop(
        "google_oauth_state",
        None
    )

    # --------------------------------------------------------
    # Go to profile
    # --------------------------------------------------------

    return redirect(
        url_for("user.profile")
    )
