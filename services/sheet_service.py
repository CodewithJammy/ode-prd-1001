import os
import json
import gspread

from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]


def get_sheet():

    spreadsheet_id = os.getenv("GOOGLE_SHEET_ID")
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    if not spreadsheet_id:
        raise RuntimeError(
            "GOOGLE_SHEET_ID is not configured in Azure."
        )

    if not service_account_json:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON is not configured in Azure."
        )

    try:
        service_account_info = json.loads(service_account_json)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_JSON contains invalid JSON."
        ) from e

    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES
    )

    client = gspread.authorize(credentials)

    spreadsheet = client.open_by_key(spreadsheet_id)

    worksheet = spreadsheet.worksheet("Users")

    return worksheet
