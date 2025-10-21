import requests
import os

class IPFSClient:
    def __init__(self):
        # Replace with your own Infura credentials
        self.project_id = "2ce17c32eee141759c06e7a7fb62b199"
        self.project_secret = "utDvYXlhLdYNm0AH4f8PqmD0w67q9oE2EvTGYwTFd2L/jOWMwcxDRg"

        # Base URL for Infura IPFS API
        self.base_url = "https://ipfs.infura.io:5001/api/v0"

        # Basic auth tuple
        self.auth = (self.project_id, self.project_secret)

    def upload_file(self, file_path):
        """Upload a file to Infura IPFS"""
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{self.base_url}/add", files=files, auth=self.auth)
        result = response.json()
        return result["Hash"]

    def download_file(self, ipfs_hash, download_folder="downloads"):
        """Download a file from Infura IPFS"""
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        url = f"https://ipfs.io/ipfs/{ipfs_hash}"  # public gateway
        response = requests.get(url)
        if response.status_code == 200:
            # Use the hash as filename
            filename = os.path.join(download_folder, ipfs_hash)
            with open(filename, "wb") as f:
                f.write(response.content)
            return filename
        else:
            raise Exception(f"Failed to download file: {response.status_code}")
