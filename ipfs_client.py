import os
import requests
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("INFURA_PROJECT_ID")
PROJECT_SECRET = os.getenv("INFURA_PROJECT_SECRET")

INFURA_IPFS_API = "https://ipfs.infura.io:5001/api/v0/add"

def upload_file(file_path):
    with open(file_path, "rb") as f:
        response = requests.post(
            INFURA_IPFS_API,
            files={"file": f},
            auth=(PROJECT_ID, PROJECT_SECRET)
        )
    
    if response.status_code == 200:
        result = response.json()
        return result["Hash"]
    else:
        raise Exception(f"Upload failed: {response.status_code} - {response.text}")
