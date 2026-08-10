import os
from flask import Blueprint, render_template, request
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient

# Create blueprint
upload_bp = Blueprint("upload", __name__, url_prefix="/upload")

@upload_bp.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        category = request.form["category"]
        subcategory = request.form["subcategory"]
        subject = request.form["subject"]
        file = request.files["questions_file"]

        # Save directly to Blob
        blob_path = save_data_file(category, subcategory, subject, file)
        return f"File uploaded to {blob_path}"

    # Pass config base URL to template
    config_base_url = f"https://{os.getenv('AZURE_STORAGE_ACCOUNT')}.blob.core.windows.net/{os.getenv('AZURE_CONFIG_CONTAINER')}"
    return render_template("upload.html", config_base_url=config_base_url)


def save_data_file(category, subcategory, subject, file):
    # Ensure safe filename
    filename = secure_filename(file.filename)

    # Build Blob path (category/subcategory/subject/filename)
    blob_path = f"{category}/{subcategory}/{subject}/{filename}"

    # Connect to Azure Blob
    blob_service_client = BlobServiceClient.from_connection_string(
        os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    )
    container_name = os.getenv("AZURE_DATA_CONTAINER")
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_path)

    # Upload directly from file stream
    blob_client.upload_blob(file, overwrite=True)

    return blob_path
