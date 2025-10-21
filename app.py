import os
import time
from flask import Flask, render_template, request, send_file, redirect, url_for
from ipfs_client import IPFSClient  # Make sure this file exists in your project

# ---------------- Blockchain ----------------
class Block:
    def __init__(self, index, timestamp, filename, ipfs_hash, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.filename = filename
        self.ipfs_hash = ipfs_hash
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        import hashlib
        value = f"{self.index}{self.timestamp}{self.filename}{self.ipfs_hash}{self.previous_hash}"
        return hashlib.sha256(value.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        # Genesis block
        self.create_block("Genesis File", "QmGenesisHash")

    def create_block(self, filename, ipfs_hash):
        timestamp = time.time()
        index = len(self.chain)
        previous_hash = self.chain[-1].hash if self.chain else "0"
        new_block = Block(index, timestamp, filename, ipfs_hash, previous_hash)
        self.chain.append(new_block)
        return new_block

# ---------------- Flask App ----------------
app = Flask(__name__)
ipfs_client = IPFSClient()
blockchain = Blockchain()
UPLOAD_FOLDER = "uploads"
DOWNLOAD_FOLDER = "downloads"

# Create folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Jinja filter to convert timestamp
@app.template_filter('timestamp_to_string')
def timestamp_to_string(ts):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))

# Home page
@app.route("/")
def index():
    chain = blockchain.chain
    return render_template("index.html", chain=chain)

# Upload file
@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Upload to IPFS
    ipfs_hash = ipfs_client.upload_file(file_path)

    # Add to blockchain
    blockchain.create_block(file.filename, ipfs_hash)

    return redirect(url_for('index'))

# Download file
@app.route("/download", methods=["POST"])
def download_file():
    ipfs_hash = request.form.get("ipfs_hash", "").strip()
    if ipfs_hash == "":
        return redirect(url_for('index'))

    try:
        path = ipfs_client.download_file(ipfs_hash, DOWNLOAD_FOLDER)
        # Send file as attachment
        filename = os.path.basename(path)
        return send_file(path, as_attachment=True, download_name=filename)
    except Exception as e:
        return f"Error downloading file: {str(e)}"

# ---------------- Run App ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
