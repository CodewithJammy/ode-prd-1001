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
from azure.storage.blob import BlobServiceClient


upload_bp = Blueprint(
    "upload",
    __name__,
    url_prefix="/upload"
)


@upload_bp.route("/", methods=["GET", "POST"])
def upload_file():

    if request.method == "POST":

        try:
            # -----------------------------
            # Get form values
            # -----------------------------
            category = request.form.get("category", "").strip()
            subcategory = request.form.get("subcategory", "").strip()
            subject = request.form.get("subject", "").strip()

            uploaded_file = request.files.get("questions_file")

            current_app.logger.info(
                f"Upload request received: "
                f"category={category}, "
                f"subcategory={subcategory}, "
                f"subject={subject}, "
                f"file={uploaded_file.filename if uploaded_file else None}"
            )

            # -----------------------------
            # Validate form
            # -----------------------------
            if not category:
                flash("Category is required.", "danger")
                return redirect(url_for("upload.upload_file"))

            if not subcategory:
                flash("Subcategory is required.", "danger")
                return redirect(url_for("upload.upload_file"))

            if not subject:
                flash("Subject is required.", "danger")
                return redirect(url_for("upload.upload_file"))

            if not uploaded_file:
                flash("Please select a file.", "danger")
                return redirect(url_for("upload.upload_file"))

            if uploaded_file.filename == "":
                flash("Please select a file.", "danger")
                return redirect(url_for("upload.upload_file"))

            # -----------------------------
            # Save to Azure Blob
            # -----------------------------
            blob_path = save_data_file(
                category,
                subcategory,
                subject,
                uploaded_file
            )

            current_app.logger.info(
                f"SUCCESS: File uploaded: {blob_path}"
            )

            flash(
                f"✅ File uploaded successfully: {blob_path}",
                "success"
            )

            return redirect(url_for("upload.upload_file"))

        except Exception as e:

            current_app.logger.exception(
                "ERROR while uploading file"
            )

            flash(
                f"❌ Upload failed: {str(e)}",
                "danger"
            )

            return redirect(url_for("upload.upload_file"))

    # -----------------------------
    # GET request
    # -----------------------------
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT")
    config_container = os.getenv("AZURE_CONFIG_CONTAINER")

    config_base_url = ""

    if storage_account and config_container:
        config_base_url = (
            f"https://{storage_account}.blob.core.windows.net/"
            f"{config_container}"
        )

    return render_template(
        "upload.html",
        config_base_url=config_base_url
    )


def save_data_file(category, subcategory, subject, file):

    # -----------------------------
    # Get environment variables
    # -----------------------------
    connection_string = os.getenv(
        "AZURE_STORAGE_CONNECTION_STRING"
    )

    container_name = os.getenv(
        "AZURE_DATA_CONTAINER"
    )

    # -----------------------------
    # Check configuration
    # -----------------------------
    if not connection_string:
        raise Exception(
            "AZURE_STORAGE_CONNECTION_STRING is not configured"
        )

    if not container_name:
        raise Exception(
            "AZURE_DATA_CONTAINER is not configured"
        )

    current_app.logger.info(
        f"Azure container: {container_name}"
    )

    # -----------------------------
    # Secure filename
    # -----------------------------
    filename = secure_filename(file.filename)

    if not filename:
        raise Exception("Invalid filename")

    # -----------------------------
    # Create blob path
    # -----------------------------
    blob_path = (
        f"data/"
        f"{category}/"
        f"{subcategory}/"
        f"{subject}/"
        f"{filename}"
    )

    current_app.logger.info(
        f"Uploading blob: {blob_path}"
    )

    # -----------------------------
    # Create BlobServiceClient
    # -----------------------------
    blob_service_client = (
        BlobServiceClient.from_connection_string(
            connection_string
        )
    )

    # -----------------------------
    # Get container client
    # -----------------------------
    container_client = (
        blob_service_client.get_container_client(
            container_name
        )
    )

    # -----------------------------
    # Check container
    # -----------------------------
    if not container_client.exists():
        raise Exception(
            f"Azure Blob container '{container_name}' does not exist"
        )

    # -----------------------------
    # Get blob client
    # -----------------------------
    blob_client = blob_service_client.get_blob_client(
        container=container_name,
        blob=blob_path
    )

    # -----------------------------
    # Upload
    # -----------------------------
    file.stream.seek(0)

    blob_client.upload_blob(
        file.stream,
        overwrite=True
    )

    current_app.logger.info(
        f"SUCCESS: Uploaded {blob_path}"
    )

    return blob_path
