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

CLIENT_ID = os.getenv(
    "GOOGLE_CLIENT_ID"
)

CLIENT_SECRET = os.getenv(
    "GOOGLE_CLIENT_SECRET"
)


# IMPORTANT:
# This must exactly match the URI configured
# in Google Cloud Console.
# ============================================================

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

    google_id = session.get(
        "google_id"
    )

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

    if not CLIENT_ID:

        return (
            "GOOGLE_CLIENT_ID is missing "
            "from Azure App Settings.",
            500
        )

    if not CLIENT_SECRET:

        return (
            "GOOGLE_CLIENT_SECRET is missing "
            "from Azure App Settings.",
            500
        )

    # --------------------------------------------------------
    # Generate PKCE code verifier
    #
    # This value must be preserved until the callback.
    # --------------------------------------------------------

    code_verifier = secrets.token_urlsafe(
        64
    )

    # --------------------------------------------------------
    # Create OAuth flow
    #
    # IMPORTANT:
    # Pass the code verifier here.
    # --------------------------------------------------------

    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        code_verifier=code_verifier
    )

    # --------------------------------------------------------
    # Use exact Azure callback URL
    # --------------------------------------------------------

    flow.redirect_uri = REDIRECT_URI

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
    # Save OAuth state
    # --------------------------------------------------------

    session["google_oauth_state"] = state

    # --------------------------------------------------------
    # Save PKCE verifier
    #
    # We need the SAME verifier when Google sends
    # the user back to /google/callback.
    # --------------------------------------------------------

    session["google_code_verifier"] = (
        code_verifier
    )

    # --------------------------------------------------------
    # Debug information
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Get PKCE code verifier
    # --------------------------------------------------------

    code_verifier = session.get(
        "google_code_verifier"
    )

    # --------------------------------------------------------
    # Validate OAuth state
    # --------------------------------------------------------

    if not state:

        return (
            "Google login session expired. "
            "Please start the login again.",
            400
        )

    # --------------------------------------------------------
    # Validate PKCE verifier
    # --------------------------------------------------------

    if not code_verifier:

        return (
            "Google OAuth code verifier is missing. "
            "Please start the login again.",
            400
        )

    # --------------------------------------------------------
    # Create OAuth flow again
    #
    # IMPORTANT:
    # Use the SAME code verifier that was generated
    # before sending the user to Google.
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Debug
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Exchange authorization code for token
    # --------------------------------------------------------

    flow.fetch_token(
        authorization_response=request.url
    )

    # --------------------------------------------------------
    # Get credentials
    # --------------------------------------------------------

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
    # Get Google unique ID
    # --------------------------------------------------------

    google_id = google_user.get(
        "sub"
    )

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
    # User does not exist
    #
    # Create new user in Google Sheet.
    # --------------------------------------------------------

    if not user:

        user = create_user(
            google_user
        )

    # --------------------------------------------------------
    # Store login information in Flask session
    # --------------------------------------------------------

    session["user_id"] = (
        user["UserId"]
    )

    session["google_id"] = (
        google_id
    )

    session["user"] = (
        user
    )

    # --------------------------------------------------------
    # Remove temporary OAuth information
    # --------------------------------------------------------

    session.pop(
        "google_oauth_state",
        None
    )

    session.pop(
        "google_code_verifier",
        None
    )

    # --------------------------------------------------------
    # Go to profile
    # --------------------------------------------------------

    return redirect(
        url_for("user.profile")
    )
