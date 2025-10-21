import os
import requests
from dotenv import load_dotenv

load_dotenv()

INFURA_PROJECT_ID = os.getenv("INFURA_PROJECT_ID")
INFURA_PROJECT_SECRET = os.getenv("INFURA_PROJECT_SECRET")

# Infura IPFS endpoint
INFURA_IPFS_URL = "https://ipfs.infura.io:5001/api/v0/add"

def upload_file(file_path):
    with open(file_path, "rb") as f:
        files = {"file": f}
        auth = (INFURA_PROJECT_ID, INFURA_PROJECT_SECRET)
        response = requests.post(INFURA_IPFS_URL, files=files, auth=auth)

    print("DEBUG status code:", response.status_code)
    print("DEBUG text:", response.text)

    if response.status_code == 200 and "Hash" in response.text:
        try:
            result = response.json()
            return result["Hash"]
        except Exception:
            # fallback: extract hash manually
            return response.text.split('"Hash":"')[1].split('"')[0]
    else:
        raise Exception(f"IPFS upload failed: {response.text}")
