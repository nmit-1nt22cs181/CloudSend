import os
from flask import Flask, render_template, request, redirect, url_for
import requests
from datetime import datetime

app = Flask(__name__)

# ------------------ IPFS Client ------------------
class IPFSClient:
    def __init__(self):
        # Hardcode your Filebase API key and endpoint
        self.api_key = "119A3E62CFD56056C119"  # replace with your key
        self.api_url = "https://api.filebase.io/v1/buckets/cloud-send-sanjith/objects"  # replace with your bucket

        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

    def upload_file(self, file_path):
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            files = {
                "file": (file_name, f)
            }
            response = requests.post(f"{self.api_url}/{file_name}", headers=self.headers, files=files)
        
        if response.status_code in [200, 201]:
            # File uploaded successfully
            return response.json()["cid"] if "cid" in response.json() else file_name
        else:
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")

# initialize client
ipfs_client = IPFSClient()

# ------------------ Jinja Filter ------------------
def timestamp_to_string(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

app.jinja_env.filters['timestamp_to_string'] = timestamp_to_string

# ------------------ Routes ------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))

    if file:
        file_path = os.path.join("uploads", file.filename)
        os.makedirs("uploads", exist_ok=True)
        file.save(file_path)

        try:
            ipfs_hash = ipfs_client.upload_file(file_path)
            return render_template("index.html", ipfs_hash=ipfs_hash)
        except Exception as e:
            return f"Error uploading file: {str(e)}"

# ------------------ Run App ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
