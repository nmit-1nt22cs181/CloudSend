# app.py
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import logging
from ipfs_client import IPFSClient
from blockchain import Blockchain

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip', 'mp4', 'mp3'}

# Ensure the uploads folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize IPFS client and blockchain
ipfs_client = IPFSClient()
blockchain = Blockchain()

# Load existing blockchain from file if it exists
blockchain.load_from_file()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.template_filter('timestamp_to_string')
def timestamp_to_string(timestamp):
    """Convert Unix timestamp to readable string"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return 'File too large (max 16MB)', 413

@app.route("/", methods=["GET"])
def index():
    """Main page with upload form and blockchain display"""
    chain = blockchain.get_chain()
    return render_template("index.html", chain=chain)

@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload to IPFS and add to blockchain"""
    if "file" not in request.files:
        logger.warning("No file part in request")
        return "No file part", 400

    file = request.files["file"]
    if file.filename == "":
        logger.warning("No file selected")
        return "No selected file", 400

    # Secure the filename
    filename = secure_filename(file.filename)
    
    # Additional security checks
    if not filename or '..' in filename or filename.startswith('/'):
        logger.warning(f"Invalid filename attempted: {filename}")
        return "Invalid filename", 400
    
    # Check file extension
    if not allowed_file(filename):
        logger.warning(f"File type not allowed: {filename}")
        return f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}", 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        # Save file temporarily
        file.save(file_path)
        logger.info(f"File saved temporarily: {filename}")
        
        # Upload to IPFS
        ipfs_hash = ipfs_client.upload_file(file_path)
        logger.info(f"File uploaded to IPFS: {filename}, CID: {ipfs_hash}")
        
        # Add to blockchain
        blockchain.create_block(filename, ipfs_hash)
        blockchain.save_to_file()  # Persist blockchain
        logger.info(f"Block added to blockchain for file: {filename}")
        
        return f"File uploaded successfully! IPFS CID: {ipfs_hash}"
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return f"Error uploading file: {str(e)}", 500
        
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Temporary file cleaned up: {filename}")

@app.route("/download", methods=["POST"])
def download_file():
    """Redirect to IPFS gateway for file download"""
    ipfs_hash = request.form.get("ipfs_hash")
    
    if not ipfs_hash:
        logger.warning("No IPFS hash provided for download")
        return "No IPFS hash provided", 400
    
    # Basic validation of IPFS hash format (CIDv0 or CIDv1)
    if not ipfs_hash or len(ipfs_hash) < 10:
        logger.warning(f"Invalid IPFS hash format: {ipfs_hash}")
        return "Invalid IPFS hash format", 400
    
    logger.info(f"Redirecting to IPFS gateway for hash: {ipfs_hash}")
    # Redirect to Filebase IPFS gateway
    return redirect(f"https://ipfs.filebase.io/ipfs/{ipfs_hash}")

@app.route("/validate", methods=["GET"])
def validate_blockchain():
    """Validate blockchain integrity"""
    is_valid = blockchain.is_valid()
    if is_valid:
        logger.info("Blockchain validation: VALID")
        return {"status": "valid", "message": "Blockchain is valid"}, 200
    else:
        logger.warning("Blockchain validation: INVALID")
        return {"status": "invalid", "message": "Blockchain has been tampered with!"}, 400

if __name__ == "__main__":
    # Use environment variable for debug mode, default to False for safety
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)