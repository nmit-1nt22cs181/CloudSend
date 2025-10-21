import os
import requests
from dotenv import load_dotenv

load_dotenv()

INFURA_PROJECT_ID = os.getenv("INFURA_PROJECT_ID")
INFURA_PROJECT_SECRET = os.getenv("INFURA_PROJECT_SECRET")
INFURA_IPFS_URL = "https://ipfs.infura.io:5001/api/v0/add"

class IPFSClient:
    def __init__(self):
        self.project_id = INFURA_PROJECT_ID
        self.project_secret = INFURA_PROJECT_SECRET
        self.api_url = INFURA_IPFS_URL

    def upload_file(self, file_path):
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(
                self.api_url,
                files=files,
                auth=(self.project_id, self.project_secret)
            )

        # ✅ Check response status and handle errors safely
        if response.status_code != 200:
            print("Error uploading to IPFS:", response.text)
            raise Exception(f"Upload failed with status code {response.status_code}")

        try:
            result = response.json()
            return result["Hash"]
        except requests.exceptions.JSONDecodeError:
            print("Non-JSON response from Infura:", response.text)
            raise Exception("Failed to parse IPFS response")
