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
    # Get test information
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
    # If pending_test exists, use the actual result
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

    payments = payments_sheet.get_all_records()

    now = datetime.utcnow()

    active_all_expiry = None


    for payment in payments:

        if str(
            payment.get(
                "GoogleId",
                ""
            )
        ).strip() != str(
            google_id
        ).strip():

            continue


        if str(
            payment.get(
                "PaymentStatus",
                ""
            )
        ).strip().lower() not in [
            "success",
            "approved"
        ]:

            continue


        if str(
            payment.get(
                "AccessType",
                ""
            )
        ).strip().lower() != "all":

            continue


        expiry_text = str(
            payment.get(
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
    # We create it now because we need AttemptId
    # for the payment request.
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


    # ========================================================
    # CREATE PAYMENT REQUEST
    # ========================================================

    payment = create_payment_request(

        attempt_id=attempt.get(
            "AttemptId"
        ),

        user_id=user_id,

        google_id=google_id,

        amount=amount,

        payment_method="Manual"
    )


    # ========================================================
    # SAVE PAYMENT INFORMATION
    # ========================================================

    session["pending_payment"] = {

        "PaymentId": payment.get(
            "PaymentId"
        ),

        "AttemptId": attempt.get(
            "AttemptId"
        ),

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
