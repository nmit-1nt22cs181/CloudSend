import os
import requests
from dotenv import load_dotenv

load_dotenv()

INFURA_PROJECT_ID = os.getenv("INFURA_PROJECT_ID")
INFURA_PROJECT_SECRET = os.getenv("INFURA_PROJECT_SECRET")

class IPFSClient:
    def __init__(self):
        self.api_url = "https://ipfs.infura.io:5001/api/v0/add"
        self.auth = (INFURA_PROJECT_ID, INFURA_PROJECT_SECRET)

    def upload_file(self, file_path):
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(self.api_url, files=files, auth=self.auth)

        print("\n--- INFURA IPFS RESPONSE DEBUG ---")
        print("Status Code:", response.status_code)
        print("Raw Response:", response.text)
        print("----------------------------------\n")

        if response.status_code != 200:
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")

        try:
            result = response.json()
            print("Parsed JSON:", result)
            return result["Hash"]
        except requests.exceptions.JSONDecodeError:
            raise Exception("Invalid JSON from Infura. Full response printed above.")
