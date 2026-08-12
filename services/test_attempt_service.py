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
        "PaymentPending",
        "",
        "",
        created_at
    ]

    sheet.append_row(row)

    return {
        "AttemptId": attempt_id,
        "Status": "PaymentPending"
    }


# ============================================================
# CREATE PAYMENT REQUEST
# ============================================================

def create_payment_request(
    attempt_id,
    user_id,
    google_id,
    amount,
    payment_method="Cash"
):

    sheet = get_payments_sheet()

    payment_id = get_next_payment_id()

    created_at = datetime.utcnow().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    row = [
        payment_id,
        attempt_id,
        user_id,
        google_id,
        amount,
        payment_method,
        "Pending",
        created_at,
        ""
    ]

    sheet.append_row(row)

    return {
        "PaymentId": payment_id,
        "AttemptId": attempt_id,
        "PaymentStatus": "Pending"
    }


# ============================================================
# APPROVE PAYMENT
# ============================================================

def approve_payment(
    payment_id
):

    payments_sheet = get_payments_sheet()
    attempts_sheet = get_test_attempts_sheet()

    payments = payments_sheet.get_all_records()

    payment = None
    payment_row_number = None

    for index, row in enumerate(
        payments,
        start=2
    ):

        if str(
            row.get("PaymentId", "")
        ).strip() == str(
            payment_id
        ).strip():

            payment = row
            payment_row_number = index
            break

    if not payment:
        return None

    # --------------------------------------------------------
    # Approve payment
    # --------------------------------------------------------

    headers = payments_sheet.row_values(1)

    if "PaymentStatus" in headers:

        column_number = (
            headers.index("PaymentStatus") + 1
        )

        payments_sheet.update_cell(
            payment_row_number,
            column_number,
            "Approved"
        )

    if "ApprovedAt" in headers:

        column_number = (
            headers.index("ApprovedAt") + 1
        )

        approved_at = datetime.utcnow()

        payments_sheet.update_cell(
            payment_row_number,
            column_number,
            approved_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

    # --------------------------------------------------------
    # Update test attempt
    # --------------------------------------------------------

    attempts = attempts_sheet.get_all_records()

    attempt_row_number = None

    for index, row in enumerate(
        attempts,
        start=2
    ):

        if str(
            row.get("AttemptId", "")
        ).strip() == str(
            payment.get("AttemptId", "")
        ).strip():

            attempt_row_number = index
            break

    if attempt_row_number is None:
        return None

    now = datetime.utcnow()

    expiry_date = now + timedelta(
        days=90
    )

    attempt_headers = (
        attempts_sheet.row_values(1)
    )

    updates = {
        "Status": "Paid",
        "AccessStartDate": now.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "ExpiryDate": expiry_date.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    for column_name, value in updates.items():

        if column_name in attempt_headers:

            column_number = (
                attempt_headers.index(
                    column_name
                ) + 1
            )

            attempts_sheet.update_cell(
                attempt_row_number,
                column_number,
                value
            )

    return {
        "AttemptId": payment.get("AttemptId"),
        "Status": "Paid",
        "AccessStartDate": now,
        "ExpiryDate": expiry_date
    }
