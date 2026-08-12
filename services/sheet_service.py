import os
import json

import gspread

from google.oauth2.service_account import Credentials


# ============================================================
# Google Sheets permissions
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]


# ============================================================
# Create Google Sheets client
# ============================================================

def get_client():

    service_account_json = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_JSON"
    )

    if not service_account_json:

        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON is not configured."
        )

    try:

        credentials_info = json.loads(
            service_account_json
        )

    except json.JSONDecodeError as e:

        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON contains invalid JSON."
        ) from e

    credentials = (
        Credentials.from_service_account_info(
            credentials_info,
            scopes=SCOPES
        )
    )

    return gspread.authorize(
        credentials
    )


# ============================================================
# Open Google Spreadsheet
# ============================================================

def get_spreadsheet():

    spreadsheet_id = os.getenv(
        "GOOGLE_SHEET_ID"
    )

    if not spreadsheet_id:

        raise RuntimeError(
            "GOOGLE_SHEET_ID is not configured."
        )

    client = get_client()

    return client.open_by_key(
        spreadsheet_id
    )


# ============================================================
# Get specific worksheet
# ============================================================

def get_worksheet(name):

    spreadsheet = get_spreadsheet()

    return spreadsheet.worksheet(
        name
    )
