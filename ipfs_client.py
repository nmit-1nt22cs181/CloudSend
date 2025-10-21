import requests
import base64
import os

class IPFSClient:
    def __init__(self):
        # ===== HARD-CODED INFURA CREDENTIALS =====
        project_id = "2ce17c32eee141759c06e7a7fb62b199"       # Replace with your Infura Project ID
        project_secret = "utDvYXlhLdYNm0AH4f8PqmD0w67q9oE2EvTGYwTFd2L/jOWMwcxDRg"  # Replace with your Infura Project Secret

        auth_string = f"{project_id}:{project_secret}"
        self.auth_header = {
            "Authorization": "Basic " + base64.b64encode(auth_string.encode()).decode()
        }
        self.api_url = "https://ipfs.infura.io:5001/api/v0"

    def upload_file(self, file_path):
        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                response = requests.post(f"{self.api_url}/add", files=files, headers=self.auth_header)

            if response.status_code != 200:
                raise Exception(f"Upload failed: {response.status_code} - {response.text}")

            result = response.json()
            return result["Hash"]

        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
