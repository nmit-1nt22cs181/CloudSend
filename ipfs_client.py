import requests

class IPFSClient:
    def __init__(self):
        # Replace this with your actual Filebase secret key
        self.api_key = "MTE5QTNFNjJDRkQ1NjA1NkMxMTk6N3U2cU5pNnAzU1h1ZjZhQVI2TEdIVXVZVjZKbEVQTXBtY3B3OFh6TTpjbG91ZC1zZW5kLXNhbmppdGg="
        self.api_url = "https://api.filebase.io/v1/ipfs"

    def upload_file(self, file_path):
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        files = {"file": open(file_path, "rb")}
        response = requests.post(f"{self.api_url}/add", headers=headers, files=files)

        if response.status_code == 200:
            result = response.json()
            print("Upload success:", result)
            return result["cid"]
        else:
            print("Upload failed:", response.status_code, response.text)
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")
