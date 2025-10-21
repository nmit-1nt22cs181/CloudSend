from flask import Flask, render_template, request, redirect, url_for
import os
from ipfs_client import IPFSClient
from werkzeug.utils import secure_filename

# -----------------------------
# Configuration
# -----------------------------
app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # Optional: 50MB max file size

# -----------------------------
# Initialize IPFS client
# -----------------------------
ipfs_client = IPFSClient()

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return render_template("upload_error.html", error="No file part in the request.")

    file = request.files["file"]
    if file.filename == "":
        return render_template("upload_error.html", error="No file selected.")

    # Secure filename
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    try:
        # Upload file to IPFS
        ipfs_hash = ipfs_client.upload_file(file_path)
        return render_template("upload_success.html", hash=ipfs_hash, filename=filename)

    except Exception as e:
        return render_template("upload_error.html", error=str(e))


# -----------------------------
# Run locally
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
