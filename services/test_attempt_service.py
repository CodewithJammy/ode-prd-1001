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
#
# This is created before payment.
#
# Status:
# PaymentRequired
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
        attempt_id,          # AttemptId
        user_id,             # UserId
        google_id,           # GoogleId
        category_id,         # CategoryId
        subcategory_id,      # SubCategoryId
        subject_id,          # SubjectId
        contenttype_id,      # ContenttypeId
        set_name,            # SetName
        score,               # Score
        attempted,           # Attempted
        total,               # Total
        percentage,          # Percentage
        result_access,       # ResultAccess
        "PaymentRequired",   # Status
        "",                  # AccessStartDate
        "",                  # ExpiryDate
        created_at           # CreatedAt
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
# Later Razorpay success will call this same function.
#
# access_type:
#
#     "Single"
#     "All"
#
# Expiry:
#
#     90 days
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
    # Normalize access type
    # --------------------------------------------------------

    access_type = str(
        access_type
    ).strip().capitalize()

    if access_type not in [
        "Single",
        "All"
    ]:

        raise ValueError(
            "Invalid access type. "
            "Expected 'Single' or 'All'."
        )

    # --------------------------------------------------------
    # Payment ID
    # --------------------------------------------------------

    payment_id = get_next_payment_id()

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    now = datetime.utcnow()

    expiry_date = (
        now + timedelta(days=90)
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
    # Create Payment record
    # --------------------------------------------------------

    row = [
        payment_id,                 # PaymentId
        attempt_id,                 # AttemptId
        user_id,                    # UserId
        google_id,                  # GoogleId
        amount,                     # Amount
        "Manual",                   # PaymentMethod
        "Success",                  # PaymentStatus
        created_at,                 # CreatedAt
        "",                         # ApprovedAt
        access_type,                # AccessType
        access_start_date,          # AccessStartDate
        expiry_date_text,           # ExpiryDate
        razorpay_order_id,          # RazorpayOrderId
        razorpay_payment_id         # RazorpayPaymentId
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

    # --------------------------------------------------------
    # Update attempt
    # --------------------------------------------------------

    if attempt_row_number is not None:

        headers = attempts_sheet.row_values(1)

        updates = {

            "Status": "Paid",

            "AccessStartDate":
                access_start_date,

            "ExpiryDate":
                expiry_date_text
        }

        for column_name, value in updates.items():

            if column_name not in headers:
                continue

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
    # RETURN PAYMENT INFORMATION
    # ========================================================

    return {

        "PaymentId":
            payment_id,

        "AttemptId":
            attempt_id,

        "UserId":
            user_id,

        "GoogleId":
            google_id,

        "Amount":
            amount,

        "PaymentMethod":
            "Manual",

        "PaymentStatus":
            "Success",

        "AccessType":
            access_type,

        "AccessStartDate":
            now,

        "ExpiryDate":
            expiry_date
    }


# ============================================================
# CHECK ACTIVE ALL-TEST SUBSCRIPTION
#
# Returns:
#
# {
#     "active": True,
#     "expiry_date": datetime(...)
# }
#
# OR
#
# {
#     "active": False,
#     "expiry_date": None
# }
# ============================================================

def get_active_all_subscription(
    user_id,
    google_id
):

    sheet = get_payments_sheet()

    records = sheet.get_all_records()

    now = datetime.utcnow()

    active_subscription = None

    for row in records:

        # ----------------------------------------------------
        # User
        # ----------------------------------------------------

        if str(
            row.get("UserId", "")
        ).strip() != str(
            user_id
        ).strip():

            continue

        # ----------------------------------------------------
        # Google ID
        # ----------------------------------------------------

        if str(
            row.get("GoogleId", "")
        ).strip() != str(
            google_id
        ).strip():

            continue

        # ----------------------------------------------------
        # Payment status
        # ----------------------------------------------------

        payment_status = str(
            row.get("PaymentStatus", "")
        ).strip().lower()

        if payment_status not in [
            "success",
            "paid",
            "successful"
        ]:

            continue

        # ----------------------------------------------------
        # Access type
        # ----------------------------------------------------

        access_type = str(
            row.get("AccessType", "")
        ).strip().lower()

        if access_type != "all":

            continue

        # ----------------------------------------------------
        # Expiry
        # ----------------------------------------------------

        expiry_string = str(
            row.get("ExpiryDate", "")
        ).strip()

        if not expiry_string:

            continue

        try:

            expiry_date = datetime.strptime(
                expiry_string,
                "%Y-%m-%d %H:%M:%S"
            )

        except ValueError:

            continue

        # ----------------------------------------------------
        # Still active
        # ----------------------------------------------------

        if expiry_date > now:

            # Keep latest expiry if user has
            # multiple All subscriptions.

            if (
                active_subscription is None
                or expiry_date
                > active_subscription["expiry_date"]
            ):

                active_subscription = {

                    "active": True,

                    "expiry_date":
                        expiry_date,

                    "payment": row
                }

    # --------------------------------------------------------
    # Return active subscription
    # --------------------------------------------------------

    if active_subscription:

        return active_subscription

    return {

        "active": False,

        "expiry_date": None,

        "payment": None
    }


# ============================================================
# CHECK ACTIVE SINGLE TEST ACCESS
#
# Single access is connected through:
#
# Payment.AttemptId
#         ↓
# TestAttempts.AttemptId
#
# Then we verify:
#
# CategoryId
# SubCategoryId
# SubjectId
# ContenttypeId
# SetName
#
# Returns:
#
# {
#     "active": True,
#     "expiry_date": datetime(...),
#     "attempt": {...}
# }
#
# OR
#
# {
#     "active": False,
#     "expiry_date": None,
#     "attempt": None
# }
# ============================================================

def get_active_single_access(
    user_id,
    google_id,
    category_id,
    subcategory_id,
    subject_id,
    contenttype_id,
    set_name
):

    payments_sheet = get_payments_sheet()

    attempts_sheet = get_test_attempts_sheet()

    payments = (
        payments_sheet.get_all_records()
    )

    attempts = (
        attempts_sheet.get_all_records()
    )

    now = datetime.utcnow()

    active_access = None

    # ========================================================
    # CHECK PAYMENTS
    # ========================================================

    for payment in payments:

        # ----------------------------------------------------
        # User
        # ----------------------------------------------------

        if str(
            payment.get("UserId", "")
        ).strip() != str(
            user_id
        ).strip():

            continue

        # ----------------------------------------------------
        # Google ID
        # ----------------------------------------------------

        if str(
            payment.get("GoogleId", "")
        ).strip() != str(
            google_id
        ).strip():

            continue

        # ----------------------------------------------------
        # Payment must be successful
        # ----------------------------------------------------

        payment_status = str(
            payment.get(
                "PaymentStatus",
                ""
            )
        ).strip().lower()

        if payment_status not in [
            "success",
            "paid",
            "successful"
        ]:

            continue

        # ----------------------------------------------------
        # Must be Single access
        # ----------------------------------------------------

        access_type = str(
            payment.get(
                "AccessType",
                ""
            )
        ).strip().lower()

        if access_type != "single":

            continue

        # ----------------------------------------------------
        # Get AttemptId
        # ----------------------------------------------------

        attempt_id = str(
            payment.get(
                "AttemptId",
                ""
            )
        ).strip()

        if not attempt_id:

            continue

        # ====================================================
        # FIND CORRESPONDING TEST ATTEMPT
        # ====================================================

        matching_attempt = None

        for attempt in attempts:

            if str(
                attempt.get(
                    "AttemptId",
                    ""
                )
            ).strip() != attempt_id:

                continue

            # ------------------------------------------------
            # Category
            # ------------------------------------------------

            if str(
                attempt.get(
                    "CategoryId",
                    ""
                )
            ).strip() != str(
                category_id
            ).strip():

                continue

            # ------------------------------------------------
            # SubCategory
            # ------------------------------------------------

            if str(
                attempt.get(
                    "SubCategoryId",
                    ""
                )
            ).strip() != str(
                subcategory_id
            ).strip():

                continue

            # ------------------------------------------------
            # Subject
            # ------------------------------------------------

            if str(
                attempt.get(
                    "SubjectId",
                    ""
                )
            ).strip() != str(
                subject_id
            ).strip():

                continue

            # ------------------------------------------------
            # Content Type
            # ------------------------------------------------

            if str(
                attempt.get(
                    "ContenttypeId",
                    ""
                )
            ).strip() != str(
                contenttype_id
            ).strip():

                continue

            # ------------------------------------------------
            # Set
            # ------------------------------------------------

            if str(
                attempt.get(
                    "SetName",
                    ""
                )
            ).strip() != str(
                set_name
            ).strip():

                continue

            matching_attempt = attempt

            break

        # ----------------------------------------------------
        # No matching attempt
        # ----------------------------------------------------

        if matching_attempt is None:

            continue

        # ====================================================
        # CHECK PAYMENT EXPIRY
        # ====================================================

        expiry_string = str(
            payment.get(
                "ExpiryDate",
                ""
            )
        ).strip()

        if not expiry_string:

            continue

        try:

            expiry_date = datetime.strptime(
                expiry_string,
                "%Y-%m-%d %H:%M:%S"
            )

        except ValueError:

            continue

        # ----------------------------------------------------
        # Still active
        # ----------------------------------------------------

        if expiry_date > now:

            # Keep latest valid access if multiple
            # payments exist for same test.

            if (
                active_access is None
                or expiry_date
                > active_access["expiry_date"]
            ):

                active_access = {

                    "active": True,

                    "expiry_date":
                        expiry_date,

                    "attempt":
                        matching_attempt,

                    "payment":
                        payment
                }

    # ========================================================
    # RETURN ACTIVE ACCESS
    # ========================================================

    if active_access:

        return active_access

    return {

        "active": False,

        "expiry_date": None,

        "attempt": None,

        "payment": None
    }


# ============================================================
# SIMPLE SINGLE ACCESS CHECK
#
# Kept for compatibility if another route is already
# calling has_valid_single_access().
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

        # ----------------------------------------------------
        # User
        # ----------------------------------------------------

        if str(
            row.get("UserId", "")
        ).strip() != str(
            user_id
        ).strip():

            continue

        # ----------------------------------------------------
        # Google ID
        # ----------------------------------------------------

        if str(
            row.get("GoogleId", "")
        ).strip() != str(
            google_id
        ).strip():

            continue

        # ----------------------------------------------------
        # Attempt
        # ----------------------------------------------------

        if str(
            row.get("AttemptId", "")
        ).strip() != str(
            attempt_id
        ).strip():

            continue

        # ----------------------------------------------------
        # Access type
        # ----------------------------------------------------

        if str(
            row.get("AccessType", "")
        ).strip().lower() != "single":

            continue

        # ----------------------------------------------------
        # Payment status
        # ----------------------------------------------------

        if str(
            row.get("PaymentStatus", "")
        ).strip().lower() not in [
            "success",
            "paid",
            "successful"
        ]:

            continue

        # ----------------------------------------------------
        # Expiry
        # ----------------------------------------------------

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

        if expiry_date > now:

            return True

    return False


# ============================================================
# SIMPLE ALL ACCESS CHECK
#
# Kept for compatibility if another route is already
# calling has_valid_all_access().
# ============================================================

def has_valid_all_access(
    user_id,
    google_id
):

    result = get_active_all_subscription(
        user_id,
        google_id
    )

    return result.get(
        "active",
        False
    )
