```python
import os
import json

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app
)

from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient


# ============================================================
# BLUEPRINT
# ============================================================

upload_bp = Blueprint(
    "upload",
    __name__,
    url_prefix="/upload"
)


# ============================================================
# AZURE CONFIG
# ============================================================

CONTAINER_NAME = os.getenv(
    "AZURE_DATA_CONTAINER",
    "ode"
)

CONFIG_PREFIX = "config/"
DATA_PREFIX = "data/"


# ============================================================
# AZURE CLIENT
# ============================================================

def get_container_client():

    connection_string = os.getenv(
        "AZURE_STORAGE_CONNECTION_STRING"
    )

    if not connection_string:

        raise RuntimeError(
            "AZURE_STORAGE_CONNECTION_STRING is not configured."
        )

    service = BlobServiceClient.from_connection_string(
        connection_string
    )

    return service.get_container_client(
        CONTAINER_NAME
    )


# ============================================================
# LOAD JSON
# ============================================================

def load_json_file(filename):

    container = get_container_client()

    blob_name = (
        f"{CONFIG_PREFIX}{filename}"
    )

    blob_client = container.get_blob_client(
        blob_name
    )

    data = (
        blob_client
        .download_blob()
        .readall()
    )

    return json.loads(
        data.decode("utf-8-sig")
    )


# ============================================================
# LOAD CONFIG
# ============================================================

def load_categories():

    data = load_json_file(
        "categories.json"
    )

    return data.get(
        "Categories",
        []
    )


def load_subcategories():

    data = load_json_file(
        "subcategories.json"
    )

    return data.get(
        "SubCategories",
        []
    )


def load_subjects():

    data = load_json_file(
        "subjects.json"
    )

    return data.get(
        "Subjects",
        []
    )


# ============================================================
# FIND CATEGORY
# ============================================================

def get_category(category_id):

    for category in load_categories():

        if (
            category.get("CategoryId")
            == category_id
        ):

            return category

    return None


# ============================================================
# FIND SUBCATEGORIES
# ============================================================

def get_subcategories(category_id):

    return [

        item

        for item in load_subcategories()

        if item.get("CategoryId")
        == category_id

    ]


# ============================================================
# FIND SUBJECTS
# ============================================================

def get_subjects(subcategory_id):

    return [

        item

        for item in load_subjects()

        if item.get("SubCategoryId")
        == subcategory_id

    ]


# ============================================================
# UPLOAD PAGE
# ============================================================

@upload_bp.route(
    "/",
    methods=["GET", "POST"]
)
def upload_file():

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == "POST":

        try:

            category_id = request.form.get(
                "category_id"
            )

            subcategory_id = request.form.get(
                "subcategory_id"
            )

            subject_id = request.form.get(
                "subject_id"
            )

            set_name = request.form.get(
                "set_name"
            )

            uploaded_file = request.files.get(
                "questions_file"
            )


            # =================================================
            # BASIC VALIDATION
            # =================================================

            if not category_id:

                flash(
                    "Please select a category.",
                    "danger"
                )

                return redirect(
                    url_for("upload.upload_file")
                )


            if not subcategory_id:

                flash(
                    "Please select a subcategory.",
                    "danger"
                )

                return redirect(
                    url_for("upload.upload_file")
                )


            if not subject_id:

                flash(
                    "Please select a subject.",
                    "danger"
                )

                return redirect(
                    url_for("upload.upload_file")
                )


            if not set_name:

                flash(
                    "Please enter a set name.",
                    "danger"
                )

                return redirect(
                    url_for("upload.upload_file")
                )


            if not uploaded_file:

                flash(
                    "Please select a CSV file.",
                    "danger"
                )

                return redirect(
                    url_for("upload.upload_file")
                )


            if not uploaded_file.filename:

                flash(
                    "Selected file has no filename.",
                    "danger"
                )

                return redirect(
                    url_for("upload.upload_file")
                )


            # =================================================
            # ONLY CSV
            # =================================================

            original_filename = secure_filename(
                uploaded_file.filename
            )

            if not original_filename.lower().endswith(
                ".csv"
            ):

                flash(
                    "Only CSV files are allowed.",
                    "danger"
                )

                return redirect(
                    url_for("upload.upload_file")
                )


            # =================================================
            # VALIDATE CATEGORY
            # =================================================

            category = get_category(
                category_id
            )

            if not category:

                flash(
                    "Invalid category selected.",
                    "danger"
                )

                return redirect(
                    url_for("upload.upload_file")
                )


            # =================================================
            # VALIDATE SUBCATEGORY
            # =================================================

            subcategory = None

            for item in get_subcategories(
                category_id
            ):

                if (
                    item.get("SubCategoryId")
                    == subcategory_id
                ):

                    subcategory = item
                    break


            if not subcategory:

                flash(
                    "Invalid subcategory selected.",
                    "danger"
                )

                return redirect(
                    url_for("upload.upload_file")
                )


            # =================================================
            # VALIDATE SUBJECT
            # =================================================

            subject = None

            for item in get_subjects(
                subcategory_id
            ):

                if (
                    item.get("SubjectId")
                    == subject_id
                ):

                    subject = item
                    break


            if not subject:

                flash(
                    "Invalid subject selected.",
                    "danger"
                )

                return redirect(
                    url_for("upload.upload_file")
                )


            # =================================================
            # CLEAN SET NAME
            # =================================================

            set_name = secure_filename(
                set_name
            )

            if not set_name:

                flash(
                    "Invalid set name.",
                    "danger"
                )

                return redirect(
                    url_for("upload.upload_file")
                )


            # Remove .csv if admin entered it

            if set_name.lower().endswith(
                ".csv"
            ):

                set_name = set_name[:-4]


            # =================================================
            # FINAL BLOB PATH
            # =================================================

            blob_path = (
                f"{DATA_PREFIX}"
                f"{category_id}/"
                f"{subcategory_id}/"
                f"{subject_id}/"
                f"{set_name}.csv"
            )


            # =================================================
            # UPLOAD
            # =================================================

            container = get_container_client()

            blob_client = (
                container
                .get_blob_client(
                    blob_path
                )
            )


            uploaded_file.stream.seek(0)

            blob_client.upload_blob(
                uploaded_file.stream,
                overwrite=True
            )


            current_app.logger.info(
                f"UPLOAD SUCCESS: {blob_path}"
            )


            # =================================================
            # SUCCESS
            # =================================================

            flash(
                f"File uploaded successfully: {blob_path}",
                "success"
            )

            return redirect(
                url_for(
                    "upload.upload_file"
                )
            )


        except Exception as e:

            current_app.logger.exception(
                "UPLOAD FAILED"
            )

            flash(
                f"Upload failed: {str(e)}",
                "danger"
            )

            return redirect(
                url_for(
                    "upload.upload_file"
                )
            )


    # ========================================================
    # GET
    # ========================================================

    categories = load_categories()
    print("CATEGORIES:", categories)
    print("COUNT:", len(categories))
    return render_template(
        "upload.html",
        categories=categories
    )


# ============================================================
# API - SUBCATEGORIES
# ============================================================

@upload_bp.route(
    "/subcategories/<category_id>"
)
def get_subcategories_api(
    category_id
):

    subcategories = get_subcategories(
        category_id
    )

    return {
        "subcategories": subcategories
    }


# ============================================================
# API - SUBJECTS
# ============================================================

@upload_bp.route(
    "/subjects/<subcategory_id>"
)
def get_subjects_api(
    subcategory_id
):

    subjects = get_subjects(
        subcategory_id
    )

    return {
        "subjects": subjects
    }
```
