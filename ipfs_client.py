# ipfs_client.py
import requests

class IPFSClient:
    def __init__(self):
        self.base_url = "https://api.filebase.io/v1/ipfs"
        self.api_key = "7u6qNi6p3SXuf6aAR6LGHUuYV6JlEPMpmcpw8XzM"  # hardcoded

    def upload_file(self, file_path):
        with open(file_path, "rb") as f:
            files = {"file": f}
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.post(f"{self.base_url}/add", files=files, headers=headers)

        if response.status_code == 200:
            result = response.json()
            return result["cid"]
        else:
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")
