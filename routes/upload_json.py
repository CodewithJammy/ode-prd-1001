import os
from flask import Blueprint, render_template, request, session, redirect, url_for,jsonify,Flask

# Create blueprint
upload_bp = Blueprint("upload", __name__, url_prefix="/upload")
@upload_bp.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        category = request.form["category"]
        subcategory = request.form["subcategory"]
        subject = request.form["subject"]
        file = request.files["questions_file"]

        # Save to Blob using your access key logic
        blob_path = save_data_file(category, subcategory, subject, file)
        return f"File uploaded to {blob_path}"

    # Pass config base URL to template
    config_base_url = f"https://{os.getenv('AZURE_STORAGE_ACCOUNT')}.blob.core.windows.net/{os.getenv('AZURE_CONFIG_CONTAINER')}"
    return render_template("upload.html", config_base_url=config_base_url)
