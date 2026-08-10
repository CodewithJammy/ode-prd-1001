import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app

from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient

# Create blueprint
upload_bp = Blueprint("upload", __name__, url_prefix="/upload")

@upload_bp.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        try:
            category = request.form["category"]
            subcategory = request.form["subcategory"]
            subject = request.form["subject"]
            file = request.files["questions_file"]

            blob_path = save_data_file(category, subcategory, subject, file)
            flash(f"✅ File uploaded to {blob_path}", "success")
            return redirect(url_for("upload.upload_file"))
        except Exception as e:
            app.logger.error(f"Upload failed: {e}")
            flash(f"❌ Upload failed: {e}", "danger")
            return redirect(url_for("upload.upload_file"))

    config_base_url = f"https://{os.getenv('AZURE_STORAGE_ACCOUNT')}.blob.core.windows.net/{os.getenv('AZURE_CONFIG_CONTAINER')}"
    return render_template("upload.html", config_base_url=config_base_url)

def save_data_file(category, subcategory, subject, file):
    filename = secure_filename(file.filename)
    blob_path = f"{category}/{subcategory}/{subject}/{filename}"

    blob_service_client = BlobServiceClient.from_connection_string(
        os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    )
    container_name = os.getenv("AZURE_DATA_CONTAINER")
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)

    try:
        blob_client.upload_blob(file.stream, overwrite=True)
        current_app.logger.info(f"✅ Uploaded {blob_path}")
    except Exception as e:
        current_app.logger.error(f"❌ Upload failed: {e}")
        raise

    return blob_path
