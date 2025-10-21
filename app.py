# app.py
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
from ipfs_client import IPFSClient

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"

# Ensure the uploads folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize IPFS client
ipfs_client = IPFSClient()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")  # Make sure index.html exists in templates/

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file part", 400

    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    try:
        # Upload to IPFS
        ipfs_hash = ipfs_client.upload_file(file_path)
        return f"File uploaded successfully! IPFS CID: {ipfs_hash}"
    except Exception as e:
        return f"Error uploading file: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
