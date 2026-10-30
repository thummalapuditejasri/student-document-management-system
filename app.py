
import os
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient
from io import BytesIO

app = Flask(__name__)
app.secret_key = "student-document-secret"

CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "student-documents"

blob_service = (
    BlobServiceClient.from_connection_string(CONNECTION_STRING)
    if CONNECTION_STRING else None
)

def get_container():
    if not blob_service:
        return None

    container = blob_service.get_container_client(CONTAINER_NAME)

    if not container.exists():
        container.create_container()

    return container


@app.route("/")
def home():
    documents = []

    if blob_service:
        container = get_container()
        documents = [
            blob.name for blob in container.list_blobs()
        ]

    return render_template("index.html", documents=documents)


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("document")

    if not file or not file.filename:
        flash("Please select a document.")
        return redirect(url_for("home"))

    filename = secure_filename(file.filename)

    if not blob_service:
        flash("Azure storage is not configured yet.")
        return redirect(url_for("home"))

    container = get_container()
    container.upload_blob(filename, file, overwrite=True)

    flash("Document uploaded successfully!")
    return redirect(url_for("home"))


@app.route("/download/<filename>")
def download(filename):
    if not blob_service:
        return "Azure storage is not configured.", 503

    container = get_container()
    blob = container.get_blob_client(filename)

    data = blob.download_blob().readall()

    return send_file(
        BytesIO(data),
        download_name=filename,
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
