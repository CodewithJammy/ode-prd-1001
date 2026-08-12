from datetime import datetime, timedelta

from services.sheet_service import get_worksheet


# ============================================================
# TEST ATTEMPTS SHEET
# ============================================================

def get_test_attempts_sheet():
    return get_worksheet("TestAttempts")


# ============================================================
# PAYMENTS SHEET
# ============================================================

def get_payments_sheet():
    return get_worksheet("Payments")


# ============================================================
# NEXT ATTEMPT ID
# ============================================================

def get_next_attempt_id():

    sheet = get_test_attempts_sheet()

    records = sheet.get_all_records()

    if not records:
        return 1

    ids = []

    for row in records:

        try:
            ids.append(
                int(row.get("AttemptId"))
            )

        except (TypeError, ValueError):
            pass

    return max(ids, default=0) + 1


# ============================================================
# NEXT PAYMENT ID
# ============================================================

def get_next_payment_id():

    sheet = get_payments_sheet()

    records = sheet.get_all_records()

    if not records:
        return 1

    ids = []

    for row in records:

        try:
            ids.append(
                int(row.get("PaymentId"))
            )

        except (TypeError, ValueError):
            pass

    return max(ids, default=0) + 1


# ============================================================
# CREATE TEST ATTEMPT
# ============================================================

def create_test_attempt(
    user_id,
    google_id,
    category_id,
    subcategory_id,
    subject_id,
    contenttype_id,
    set_name,
    score,
    attempted,
    total,
    percentage,
    result_access
):

    sheet = get_test_attempts_sheet()

    attempt_id = get_next_attempt_id()

    created_at = datetime.utcnow().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    row = [
        attempt_id,
        user_id,
        google_id,
        category_id,
        subcategory_id,
        subject_id,
        contenttype_id,
        set_name,
        score,
        attempted,
        total,
        percentage,
        result_access,
        "PaymentRequired",
        "",
        "",
        created_at
    ]

    sheet.append_row(row)

    return {
        "AttemptId": attempt_id,
        "Status": "PaymentRequired"
    }


# ============================================================
# CREATE SUCCESSFUL PAYMENT
#
# TEMPORARY PAYMENT SIMULATION
#
# Later Razorpay will call this after successful
# payment verification.
# ============================================================

def create_successful_payment(
    attempt_id,
    user_id,
    google_id,
    amount,
    access_type,
    razorpay_order_id="",
    razorpay_payment_id=""
):

    payments_sheet = get_payments_sheet()
    attempts_sheet = get_test_attempts_sheet()

    # --------------------------------------------------------
    # Payment ID
    # --------------------------------------------------------

    payment_id = get_next_payment_id()

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    now = datetime.utcnow()

    expiry_date = now + timedelta(
        days=90
    )

    created_at = now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    access_start_date = now.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    expiry_date_text = expiry_date.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # --------------------------------------------------------
    # Create payment record
    # --------------------------------------------------------

    row = [
        payment_id,
        attempt_id,
        user_id,
        google_id,
        amount,
        "Manual",
        "Success",
        created_at,
        "",
        access_type,
        access_start_date,
        expiry_date_text,
        razorpay_order_id,
        razorpay_payment_id
    ]

    payments_sheet.append_row(row)

    # ========================================================
    # UPDATE TEST ATTEMPT
    # ========================================================

    attempts = attempts_sheet.get_all_records()

    attempt_row_number = None

    for index, row in enumerate(
        attempts,
        start=2
    ):

        if str(
            row.get("AttemptId", "")
        ).strip() == str(
            attempt_id
        ).strip():

            attempt_row_number = index
            break

    if attempt_row_number is not None:

        headers = attempts_sheet.row_values(1)

        updates = {
            "Status": "Paid",
            "AccessStartDate": access_start_date,
            "ExpiryDate": expiry_date_text
        }

        for column_name, value in updates.items():

            if column_name in headers:

                column_number = (
                    headers.index(
                        column_name
                    ) + 1
                )

                attempts_sheet.update_cell(
                    attempt_row_number,
                    column_number,
                    value
                )

    # ========================================================
    # RETURN PAYMENT
    # ========================================================

    return {
        "PaymentId": payment_id,
        "AttemptId": attempt_id,
        "UserId": user_id,
        "GoogleId": google_id,
        "Amount": amount,
        "PaymentMethod": "Manual",
        "PaymentStatus": "Success",
        "AccessType": access_type,
        "AccessStartDate": now,
        "ExpiryDate": expiry_date
    }


# ============================================================
# FIND VALID SINGLE ACCESS
# ============================================================

def has_valid_single_access(
    user_id,
    google_id,
    attempt_id
):

    sheet = get_payments_sheet()

    records = sheet.get_all_records()

    now = datetime.utcnow()

    for row in records:

        if str(
            row.get("UserId", "")
        ).strip() != str(
            user_id
        ).strip():

            continue

        if str(
            row.get("GoogleId", "")
        ).strip() != str(
            google_id
        ).strip():

            continue

        if str(
            row.get("AttemptId", "")
        ).strip() != str(
            attempt_id
        ).strip():

            continue

        if str(
            row.get("AccessType", "")
        ).strip().lower() != "single":

            continue

        if str(
            row.get("PaymentStatus", "")
        ).strip().lower() != "success":

            continue

        expiry_text = str(
            row.get("ExpiryDate", "")
        ).strip()

        if not expiry_text:
            continue

        try:

            expiry_date = datetime.strptime(
                expiry_text,
                "%Y-%m-%d %H:%M:%S"
            )

        except ValueError:

            continue

        if now <= expiry_date:

            return True

    return False


# ============================================================
# FIND VALID ALL ACCESS
# ============================================================

def has_valid_all_access(
    user_id,
    google_id
):

    sheet = get_payments_sheet()

    records = sheet.get_all_records()

    now = datetime.utcnow()

    for row in records:

        if str(
            row.get("UserId", "")
        ).strip() != str(
            user_id
        ).strip():

            continue

        if str(
            row.get("GoogleId", "")
        ).strip() != str(
            google_id
        ).strip():

            continue

        if str(
            row.get("AccessType", "")
        ).strip().lower() != "all":

            continue

        if str(
            row.get("PaymentStatus", "")
        ).strip().lower() != "success":

            continue

        expiry_text = str(
            row.get("ExpiryDate", "")
        ).strip()

        if not expiry_text:
            continue

        try:

            expiry_date = datetime.strptime(
                expiry_text,
                "%Y-%m-%d %H:%M:%S"
            )

        except ValueError:

            continue

        if now <= expiry_date:

            return True

    return False
