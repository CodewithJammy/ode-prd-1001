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

upload_bp = Blueprint("upload", __name__, url_prefix="/upload")


# ============================================================
# AZURE CONFIG
# ============================================================

CONTAINER_NAME = os.getenv("AZURE_DATA_CONTAINER", "ode")
CONFIG_PREFIX = "config/"
DATA_PREFIX = "data/"


# ============================================================
# AZURE CLIENT
# ============================================================

def get_container_client():
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING is not configured.")
    service = BlobServiceClient.from_connection_string(connection_string)
    return service.get_container_client(CONTAINER_NAME)


# ============================================================
# LOAD JSON HELPERS
# ============================================================

def load_json_file(filename):
    container = get_container_client()
    blob_name = f"{CONFIG_PREFIX}{filename}"
    blob_client = container.get_blob_client(blob_name)
    data = blob_client.download_blob().readall()
    return json.loads(data.decode("utf-8-sig"))

def load_categories():
    return load_json_file("categories.json").get("Categories", [])

def load_subcategories():
    return load_json_file("subcategories.json").get("SubCategories", [])

def load_subjects():
    return load_json_file("subjects.json").get("Subjects", [])

def load_contenttypes():
    return load_json_file("contenttype.json").get("Contenttype", [])


# ============================================================
# FINDERS
# ============================================================

def get_category(category_id):
    return next((c for c in load_categories() if c.get("CategoryId") == category_id), None)

def get_subcategories(category_id):
    return [s for s in load_subcategories() if s.get("CategoryId") == category_id]

def get_subjects(subcategory_id):
    return [s for s in load_subjects() if s.get("SubCategoryId") == subcategory_id]

def get_contenttypes(subject_id):
    return [c for c in load_contenttypes() if c.get("SubjectId") == subject_id]


# ============================================================
# UPLOAD PAGE
# ============================================================

@upload_bp.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        try:
            category_id = request.form.get("category_id")
            subcategory_id = request.form.get("subcategory_id")
            subject_id = request.form.get("subject_id")
            contenttype_id = request.form.get("contenttype_id")
            set_name = request.form.get("set_name")
            uploaded_file = request.files.get("questions_file")

            # Basic validation
            if not category_id:
                flash("Please select a category.", "danger")
                return redirect(url_for("upload.upload_file"))
            if not subcategory_id:
                flash("Please select a subcategory.", "danger")
                return redirect(url_for("upload.upload_file"))
            if not contenttype_id:
                flash("Please select a content type.", "danger")
                return redirect(url_for("upload.upload_file"))
            if not set_name:
                flash("Please enter a set name.", "danger")
                return redirect(url_for("upload.upload_file"))
            if not uploaded_file or not uploaded_file.filename:
                flash("Please select a CSV file.", "danger")
                return redirect(url_for("upload.upload_file"))

            original_filename = secure_filename(uploaded_file.filename)
            if not original_filename.lower().endswith(".csv"):
                flash("Only CSV files are allowed.", "danger")
                return redirect(url_for("upload.upload_file"))

            category = get_category(category_id)
            if not category:
                flash("Invalid category selected.", "danger")
                return redirect(url_for("upload.upload_file"))

            # Validate subcategory
            subcategory = next((s for s in get_subcategories(category_id)
                                if s.get("SubCategoryId") == subcategory_id), None)
            if not subcategory:
                flash("Invalid subcategory selected.", "danger")
                return redirect(url_for("upload.upload_file"))

            # Clean set name
            set_name = secure_filename(set_name)
            if set_name.lower().endswith(".csv"):
                set_name = set_name[:-4]

            # ============================================================
            # SPECIAL CASE HANDLING
            # ============================================================
            if subcategory_id.lower() in ("oneday", "certification"):
                # Force subject_id to match subcategory for path consistency
                subject_id = subcategory_id.lower()

                # Validate contenttype normally
                contenttype = next(
                    (c for c in get_contenttypes(subject_id)
                     if c.get("ContenttypeId") == contenttype_id),
                    None
                )
                if not contenttype:
                    flash("Invalid content type selected.", "danger")
                    return redirect(url_for("upload.upload_file"))

                blob_path = (
                    f"{DATA_PREFIX}{category_id}/"
                    f"{subcategory_id}/"
                    f"{subject_id}/"
                    f"{contenttype_id}/"
                    f"{set_name}.csv"
                )

            else:
                # Normal flow → subject required
                if not subject_id:
                    flash("Please select a subject.", "danger")
                    return redirect(url_for("upload.upload_file"))

                subject = next(
                    (s for s in get_subjects(subcategory_id)
                     if s.get("SubjectId") == subject_id),
                    None
                )
                if not subject:
                    flash("Invalid subject selected.", "danger")
                    return redirect(url_for("upload.upload_file"))

                contenttype = next(
                    (c for c in get_contenttypes(subject_id)
                     if c.get("ContenttypeId") == contenttype_id),
                    None
                )
                if not contenttype:
                    flash("Invalid content type selected.", "danger")
                    return redirect(url_for("upload.upload_file"))

                blob_path = (
                    f"{DATA_PREFIX}{category_id}/"
                    f"{subcategory_id}/"
                    f"{subject_id}/"
                    f"{contenttype_id}/"
                    f"{set_name}.csv"
                )

            # ============================================================
            # UPLOAD TO AZURE
            # ============================================================
            container = get_container_client()
            blob_client = container.get_blob_client(blob_path)
            uploaded_file.stream.seek(0)
            blob_client.upload_blob(uploaded_file.stream, overwrite=True)

            current_app.logger.info(f"UPLOAD SUCCESS: {blob_path}")
            flash(f"File uploaded successfully: {blob_path}", "success")
            return redirect(url_for("upload.upload_file"))

        except Exception as e:
            current_app.logger.exception("UPLOAD FAILED")
            flash(f"Upload failed: {str(e)}", "danger")
            return redirect(url_for("upload.upload_file"))

    # GET
    categories = load_categories()
    return render_template("upload.html", categories=categories)


# ============================================================
# API ENDPOINTS
# ============================================================

@upload_bp.route("/subcategories/<category_id>")
def get_subcategories_api(category_id):
    return {"subcategories": get_subcategories(category_id)}

@upload_bp.route("/subjects/<subcategory_id>")
def get_subjects_api(subcategory_id):
    return {"subjects": get_subjects(subcategory_id)}

@upload_bp.route("/contenttypes/<subject_id>")
def get_contenttypes_api(subject_id):
    return {"contenttypes": get_contenttypes(subject_id)}

@upload_bp.route("/deployment-test")
def deployment_test():
    return "DEPLOYMENT TEST - NEW UPLOAD.PY"
