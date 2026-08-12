import os

from flask import (
    Blueprint,
    redirect,
    request,
    session,
    url_for,
    render_template
)

from google_auth_oauthlib.flow import Flow
import requests

from services.user_service import (
    find_user_by_google_id,
    create_user
)


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [
            "https://exambank.azurewebsites.net/auth/google/callback"
        ]
    }
}


SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]


@auth_bp.route("/login")
def login():

    return render_template("login.html")


@auth_bp.route("/google")
def google_login():

    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES
    )

    flow.redirect_uri = url_for(
        "auth.google_callback",
        _external=True
    )

    authorization_url, state = (
        flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="select_account"
        )
    )

    session["google_oauth_state"] = state

    return redirect(authorization_url)


@auth_bp.route("/google/callback")
def google_callback():

    state = session.get(
        "google_oauth_state"
    )

    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        state=state
    )

    flow.redirect_uri = url_for(
        "auth.google_callback",
        _external=True
    )

    flow.fetch_token(
        authorization_response=request.url
    )

    credentials = flow.credentials

    response = requests.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={
            "Authorization":
                f"Bearer {credentials.token}"
        }
    )

    response.raise_for_status()

    google_user = response.json()

    google_id = google_user["sub"]

    user = find_user_by_google_id(
        google_id
    )

    if not user:

        user = create_user(
            google_user
        )

    session["user_id"] = user["UserId"]

    session["google_id"] = google_id

    session["user"] = user

    return redirect(
        url_for("user.user_home")
    )
