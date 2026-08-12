from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    abort
)

from services.sheet_service import get_worksheet

from services.test_attempt_service import (
    create_test_attempt,
    create_payment_request
)


# ============================================================
# BLUEPRINT
# ============================================================

payment_bp = Blueprint(
    "payment",
    __name__,
    url_prefix="/payment"
)


# ============================================================
# CONSTANT
# ============================================================

ALL_TEST_PRICE = 99


# ============================================================
# PAYMENT SELECTION
# ============================================================

@payment_bp.route(
    "/select",
    methods=["POST"]
)
def select_payment():

    # --------------------------------------------------------
    # User must be logged in
    # --------------------------------------------------------

    google_id = session.get("google_id")
    user_id = session.get("user_id")

    if not google_id or not user_id:
        return redirect(
            url_for("auth.login")
        )


    # --------------------------------------------------------
    # Get selected access type
    # --------------------------------------------------------

    access_type = request.form.get(
        "access_type",
        ""
    ).strip()

    if access_type not in [
        "Single",
        "All"
    ]:
        abort(400)


    # --------------------------------------------------------
    # Get test information from form
    # --------------------------------------------------------

    category_id = request.form.get(
        "category_id"
    )

    subcategory_id = request.form.get(
        "subcategory_id"
    )

    subject_id = request.form.get(
        "subject_id"
    )

    contenttype_id = request.form.get(
        "contenttype_id"
    )

    set_name = request.form.get(
        "set_name"
    )


    # ========================================================
    # GET PENDING TEST RESULT
    # ========================================================

    pending_test = session.get(
        "pending_test"
    )


    # --------------------------------------------------------
    # If pending_test exists, use actual test result
    # --------------------------------------------------------

    if pending_test:

        category_id = pending_test.get(
            "category_id"
        )

        subcategory_id = pending_test.get(
            "subcategory_id"
        )

        subject_id = pending_test.get(
            "subject_id"
        )

        contenttype_id = pending_test.get(
            "contenttype_id"
        )

        set_name = pending_test.get(
            "set_name"
        )

        score = pending_test.get(
            "score",
            0
        )

        attempted = pending_test.get(
            "attempted",
            0
        )

        total = pending_test.get(
            "total",
            0
        )

        percentage = pending_test.get(
            "percentage",
            0
        )

    else:

        score = 0
        attempted = 0
        total = 0
        percentage = 0


    # ========================================================
    # VALIDATE REQUIRED TEST INFORMATION
    # ========================================================

    if not category_id:
        abort(400)

    if not subcategory_id:
        abort(400)

    if not subject_id:
        abort(400)

    if not contenttype_id:
        abort(400)

    if not set_name:
        abort(400)


    # ========================================================
    # LOAD CONTENT TYPE
    # ========================================================

    from routes.demo_test import (
        get_contenttype,
        get_category,
        get_subcategory,
        get_subject
    )


    category = get_category(
        category_id
    )

    subcategory = get_subcategory(
        subcategory_id
    )

    subject = get_subject(
        subcategory_id,
        subject_id
    )

    contenttype = get_contenttype(
        subject_id,
        contenttype_id
    )


    # --------------------------------------------------------
    # Validate content
    # --------------------------------------------------------

    if (
        not category
        or not subcategory
        or not subject
        or not contenttype
    ):
        abort(404)


    # ========================================================
    # DETERMINE PRICE
    # ========================================================

    if access_type == "Single":

        try:

            amount = float(
                contenttype.get(
                    "Price",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            amount = 0

    else:

        amount = ALL_TEST_PRICE


    # ========================================================
    # CHECK EXISTING ACTIVE "ALL" SUBSCRIPTION
    # ========================================================

    payments_sheet = get_worksheet(
        "Payments"
    )

    payments = (
        payments_sheet.get_all_records()
    )

    now = datetime.utcnow()

    active_all_expiry = None


    for payment_record in payments:

        # ----------------------------------------------------
        # User
        # ----------------------------------------------------

        if str(
            payment_record.get(
                "UserId",
                ""
            )
        ).strip() != str(
            user_id
        ).strip():

            continue


        # ----------------------------------------------------
        # Google ID
        # ----------------------------------------------------

        if str(
            payment_record.get(
                "GoogleId",
                ""
            )
        ).strip() != str(
            google_id
        ).strip():

            continue


        # ----------------------------------------------------
        # Payment status
        # ----------------------------------------------------

        payment_status = str(
            payment_record.get(
                "PaymentStatus",
                ""
            )
        ).strip().lower()

        if payment_status not in [
            "success",
            "paid",
            "successful",
            "approved"
        ]:

            continue


        # ----------------------------------------------------
        # Access type
        # ----------------------------------------------------

        if str(
            payment_record.get(
                "AccessType",
                ""
            )
        ).strip().lower() != "all":

            continue


        # ----------------------------------------------------
        # Expiry
        # ----------------------------------------------------

        expiry_text = str(
            payment_record.get(
                "ExpiryDate",
                ""
            )
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


        # ----------------------------------------------------
        # Still active
        # ----------------------------------------------------

        if expiry_date > now:

            if (
                active_all_expiry is None
                or expiry_date > active_all_expiry
            ):

                active_all_expiry = expiry_date


    # ========================================================
    # USER ALREADY HAS ACTIVE ALL SUBSCRIPTION
    # ========================================================

    if active_all_expiry:

        return render_template(
            "subscription_active.html",

            expiry_date=active_all_expiry,

            category=category,

            subcategory=subcategory,

            subject=subject,

            contenttype=contenttype,

            set_name=set_name
        )


    # ========================================================
    # CREATE TEST ATTEMPT
    #
    # Attempt is created before payment because
    # Payment.AttemptId needs this ID.
    # ========================================================

    attempt = create_test_attempt(

        user_id=user_id,

        google_id=google_id,

        category_id=category_id,

        subcategory_id=subcategory_id,

        subject_id=subject_id,

        contenttype_id=contenttype_id,

        set_name=set_name,

        score=score,

        attempted=attempted,

        total=total,

        percentage=percentage,

        result_access="Paid"
    )


    # --------------------------------------------------------
    # Validate attempt
    # --------------------------------------------------------

    attempt_id = attempt.get(
        "AttemptId"
    )

    if not attempt_id:

        abort(500)


    # ========================================================
    # CREATE PAYMENT REQUEST
    # ========================================================

    payment = create_payment_request(

        attempt_id=attempt_id,

        user_id=user_id,

        google_id=google_id,

        amount=amount,

        access_type=access_type,

        payment_method="Manual"
    )


    # ========================================================
    # SAVE PAYMENT INFORMATION IN SESSION
    # ========================================================

    session["pending_payment"] = {

        "AttemptId": attempt_id,

        "AccessType": access_type,

        "Amount": amount,

        "CategoryId": category_id,

        "SubCategoryId": subcategory_id,

        "SubjectId": subject_id,

        "ContenttypeId": contenttype_id,

        "SetName": set_name

    }


    # ========================================================
    # TEMPORARY PAYMENT PAGE
    # ========================================================

    return render_template(

        "manual_payment.html",

        payment=payment,

        amount=amount,

        access_type=access_type,

        category=category,

        subcategory=subcategory,

        subject=subject,

        contenttype=contenttype,

        set_name=set_name
    )
