from datetime import datetime

from services.sheet_service import get_worksheet


def get_users_sheet():

    return get_worksheet("Users")


def find_user_by_google_id(google_id):

    sheet = get_users_sheet()

    records = sheet.get_all_records()

    for row in records:

        if str(row.get("GoogleId", "")).strip() == str(google_id).strip():

            return row

    return None


def create_user(google_user):

    sheet = get_users_sheet()

    records = sheet.get_all_records()

    user_id = len(records) + 1

    row = [
        user_id,
        google_user["sub"],
        google_user["email"],
        google_user.get("name", ""),
        google_user.get("given_name", ""),
        google_user.get("family_name", ""),
        google_user.get("picture", ""),
        "",
        "",
        1,
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    ]

    sheet.append_row(row)

    return {
        "UserId": user_id,
        "GoogleId": google_user["sub"],
        "Email": google_user["email"],
        "Username": google_user.get("name", ""),
        "FirstName": google_user.get("given_name", ""),
        "LastName": google_user.get("family_name", ""),
        "Picture": google_user.get("picture", ""),
        "Mobile": "",
        "Gender": "",
        "NewUser": 1
    }
