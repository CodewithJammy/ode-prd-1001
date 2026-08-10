import os

from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    current_app
)

from werkzeug.utils import secure_filename


upload_bp = Blueprint(
    "upload",
    __name__,
    url_prefix="/upload"
)


@upload_bp.route("/", methods=["GET", "POST"])
def upload_file():

    print("========================================")
    print("UPLOAD ROUTE HIT")
    print("REQUEST METHOD:", request.method)
    print("========================================")

    # --------------------------------------
    # POST
    # --------------------------------------
    if request.method == "POST":

        print("========================================")
        print("POST REQUEST RECEIVED")
        print("========================================")

        try:
            # Print everything received from browser
            print("FORM DATA:")
            print(request.form)

            print("FILES:")
            print(request.files)

            # ----------------------------------
            # Get form values
            # ----------------------------------
            category = request.form.get("category", "")
            subcategory = request.form.get("subcategory", "")
            subject = request.form.get("subject", "")

            uploaded_file = request.files.get("questions_file")

            print("CATEGORY:", category)
            print("SUBCATEGORY:", subcategory)
            print("SUBJECT:", subject)
            print(
                "FILE:",
                uploaded_file.filename
                if uploaded_file
                else "NO FILE"
            )

            # ----------------------------------
            # Validate file
            # ----------------------------------
            if not uploaded_file:

                print("ERROR: NO FILE RECEIVED")

                flash(
                    "❌ No file received by Flask.",
                    "danger"
                )

                return redirect(
                    url_for("upload.upload_file")
                )

            if uploaded_file.filename == "":

                print("ERROR: EMPTY FILENAME")

                flash(
                    "❌ No file selected.",
                    "danger"
                )

                return redirect(
                    url_for("upload.upload_file")
                )

            # ----------------------------------
            # Secure filename
            # ----------------------------------
            filename = secure_filename(
                uploaded_file.filename
            )

            print("SECURE FILENAME:", filename)

            # ----------------------------------
            # TEMPORARY TEST ONLY
            # DO NOT UPLOAD TO AZURE YET
            # ----------------------------------

            file_content = uploaded_file.read()

            print(
                "FILE SIZE:",
                len(file_content),
                "bytes"
            )

            print("========================================")
            print("SUCCESS - FLASK RECEIVED FILE")
            print("========================================")

            flash(
                f"✅ Flask received '{filename}' "
                f"({len(file_content)} bytes)",
                "success"
            )

            return redirect(
                url_for("upload.upload_file")
            )

        except Exception as e:

            print("========================================")
            print("UPLOAD ERROR")
            print("ERROR TYPE:", type(e).__name__)
            print("ERROR:", str(e))
            print("========================================")

            current_app.logger.exception(
                "Upload test failed"
            )

            flash(
                f"❌ Upload test failed: "
                f"{type(e).__name__}: {str(e)}",
                "danger"
            )

            return redirect(
                url_for("upload.upload_file")
            )

    # --------------------------------------
    # GET
    # --------------------------------------

    print("Rendering upload page")

    return render_template("upload.html")
