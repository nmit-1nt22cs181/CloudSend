import os
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from werkzeug.utils import secure_filename
from ipfs_client import IPFSClient  # Make sure this file exists and is correct

# ----------------------------
# Flask App Setup
# ----------------------------
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ----------------------------
# Jinja2 Filter
# ----------------------------
@app.template_filter('timestamp_to_string')
def timestamp_to_string(timestamp):
    """Convert UNIX timestamp to human-readable string."""
    try:
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return "Invalid timestamp"

# ----------------------------
# Initialize IPFS client
# ----------------------------
ipfs_client = IPFSClient()  # Make sure IPFSClient is correctly set up in ipfs_client.py

# ----------------------------
# Example Blockchain Data
# ----------------------------
chain = [
    {'timestamp': 1697865600, 'data': 'Genesis Block', 'hash': 'QmExample1'},
    {'timestamp': 1697879200, 'data': 'Second Block', 'hash': 'QmExample2'},
]

# ----------------------------
# Routes
# ----------------------------
@app.route('/')
def index():
    return render_template('index.html', chain=chain)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            # Upload to IPFS
            ipfs_hash = ipfs_client.upload_file(file_path)
            # Add to blockchain (example)
            chain.append({
                'timestamp': datetime.utcnow().timestamp(),
                'data': filename,
                'hash': ipfs_hash
            })
        except Exception as e:
            return f"Upload failed: {str(e)}"

    return redirect(url_for('index'))

# ----------------------------
# Run App
# ----------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
