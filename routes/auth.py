import os
import secrets
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
# BLUEPRINT
# ============================================================

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


# ============================================================
# GOOGLE OAUTH CONFIGURATION
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

        "auth_uri": (
            "https://accounts.google.com/o/oauth2/auth"
        ),

        "token_uri": (
            "https://oauth2.googleapis.com/token"
        ),

        "redirect_uris": [
            REDIRECT_URI
        ]
    }
}


# ============================================================
# GOOGLE OAUTH SCOPES
# ============================================================

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]



# ============================================================
# LOGOUT
# ============================================================

@auth_bp.route("/logout", methods=["GET"])
def logout():

    # --------------------------------------------------------
    # Completely clear current user session
    # --------------------------------------------------------

    session.clear()

    # --------------------------------------------------------
    # Prevent browser from using cached authenticated pages
    # --------------------------------------------------------

    response = redirect(
        url_for("auth.login")
    )

    response.headers["Cache-Control"] = (
        "no-cache, no-store, must-revalidate"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response
# ============================================================
# ACCOUNT BUTTON
# ============================================================

@auth_bp.route("/account")
def account():

    # --------------------------------------------------------
    # Check whether user is already logged in
    # --------------------------------------------------------

    google_id = session.get("google_id")

    # --------------------------------------------------------
    # NOT LOGGED IN
    # Send user to login page
    # --------------------------------------------------------

    if not google_id:

        return redirect(
            url_for("auth.login")
        )

    # --------------------------------------------------------
    # ALREADY LOGGED IN
    # Send user to USER HOME
    #
    # IMPORTANT:
    # Do NOT send to profile here.
    # --------------------------------------------------------

    return redirect(
        url_for("user.user_home")
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
    # Check Google Client ID
    # --------------------------------------------------------

    if not CLIENT_ID:

        return (
            "GOOGLE_CLIENT_ID is missing "
            "from Azure App Settings.",
            500
        )

    # --------------------------------------------------------
    # Check Google Client Secret
    # --------------------------------------------------------

    if not CLIENT_SECRET:

        return (
            "GOOGLE_CLIENT_SECRET is missing "
            "from Azure App Settings.",
            500
        )

    # ========================================================
    # GENERATE PKCE CODE VERIFIER
    # ========================================================

    code_verifier = secrets.token_urlsafe(64)

    # ========================================================
    # CREATE GOOGLE OAUTH FLOW
    # ========================================================

    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        code_verifier=code_verifier
    )

    # --------------------------------------------------------
    # Exact Azure callback URL
    # --------------------------------------------------------

    flow.redirect_uri = REDIRECT_URI

    # ========================================================
    # GENERATE GOOGLE AUTHORIZATION URL
    # ========================================================

    authorization_url, state = (
        flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="select_account"
        )
    )

    # ========================================================
    # SAVE OAUTH STATE
    # ========================================================

    session["google_oauth_state"] = state

    # ========================================================
    # SAVE PKCE CODE VERIFIER
    # ========================================================

    session["google_code_verifier"] = code_verifier

    # ========================================================
    # DEBUG
    # ========================================================

    print(
        "DEBUG GOOGLE CLIENT ID:",
        CLIENT_ID
    )

    print(
        "DEBUG GOOGLE REDIRECT URI:",
        REDIRECT_URI
    )

    print(
        "DEBUG GOOGLE STATE SAVED"
    )

    print(
        "DEBUG GOOGLE CODE VERIFIER SAVED"
    )

    # ========================================================
    # REDIRECT TO GOOGLE
    # ========================================================

    return redirect(
        authorization_url
    )


# ============================================================
# GOOGLE CALLBACK
# ============================================================

@auth_bp.route("/google/callback")
def google_callback():

    # ========================================================
    # GET OAUTH STATE
    # ========================================================

    state = session.get(
        "google_oauth_state"
    )

    # ========================================================
    # GET PKCE VERIFIER
    # ========================================================

    code_verifier = session.get(
        "google_code_verifier"
    )

    # ========================================================
    # VALIDATE STATE
    # ========================================================

    if not state:

        return (
            "Google login session expired. "
            "Please start the login again.",
            400
        )

    # ========================================================
    # VALIDATE PKCE VERIFIER
    # ========================================================

    if not code_verifier:

        return (
            "Google OAuth code verifier is missing. "
            "Please start the login again.",
            400
        )

    # ========================================================
    # CREATE OAUTH FLOW AGAIN
    # ========================================================

    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        state=state,
        code_verifier=code_verifier
    )

    # --------------------------------------------------------
    # Exact Azure callback URL
    # --------------------------------------------------------

    flow.redirect_uri = REDIRECT_URI

    # ========================================================
    # DEBUG
    # ========================================================

    print(
        "DEBUG CALLBACK URL:",
        request.url
    )

    print(
        "DEBUG GOOGLE REDIRECT URI:",
        REDIRECT_URI
    )

    print(
        "DEBUG CODE VERIFIER FOUND"
    )

    # ========================================================
    # EXCHANGE AUTHORIZATION CODE
    # ========================================================

    try:

        flow.fetch_token(
            authorization_response=request.url
        )

    except Exception as e:

        print(
            "GOOGLE TOKEN ERROR:",
            str(e)
        )

        return (
            "Google login failed while exchanging "
            "the authorization code. "
            "Please try again.",
            500
        )

    # ========================================================
    # GET GOOGLE CREDENTIALS
    # ========================================================

    credentials = flow.credentials

    # ========================================================
    # GET GOOGLE USER INFORMATION
    # ========================================================

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

    # ========================================================
    # GET GOOGLE UNIQUE ID
    # ========================================================

    google_id = google_user.get(
        "sub"
    )

    if not google_id:

        return (
            "Google did not return a user ID.",
            400
        )

    # ========================================================
    # FIND USER IN GOOGLE SHEET
    # ========================================================

    user = find_user_by_google_id(
        google_id
    )

    # ========================================================
    # CREATE NEW USER
    # ========================================================

    if not user:

        user = create_user(
            google_user
        )

    # ========================================================
    # SAFETY CHECK
    # ========================================================

    if not user:

        return (
            "Unable to create or retrieve your "
            "user profile.",
            500
        )

    # ========================================================
    # STORE LOGIN SESSION
    # ========================================================

    session["user_id"] = user.get(
        "UserId"
    )

    session["google_id"] = google_id

    session["user"] = user

    # ========================================================
    # REMOVE TEMPORARY OAUTH DATA
    # ========================================================

    session.pop(
        "google_oauth_state",
        None
    )

    session.pop(
        "google_code_verifier",
        None
    )

    # ========================================================
    # IMPORTANT LOGIN FLOW
    # ========================================================
    #
    # Do NOT directly send every user to profile.
    #
    # user_home() will check NewUser:
    #
    # NewUser = 1
    #       -> profile
    #
    # NewUser = 0
    #       -> user_home.html
    #
    # ========================================================

    return redirect(
        url_for("user.user_home")
    )
