# ipfs_client.py
import requests

class IPFSClient:
    def __init__(self):
        # Filebase IPFS API endpoint
        self.api_endpoint = "https://api.filebase.io/v1/ipfs/add"
        # Hardcode your secret API key here
        self.api_key = "7u6qNi6p3SXuf6aAR6LGHUuYV6JlEPMpmcpw8XzM"  # <-- replace with your actual key

    def upload_file(self, file_path):
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                response = requests.post(self.api_endpoint, headers=headers, files=files)

            # Check for HTTP errors
            response.raise_for_status()

            # Filebase IPFS returns JSON with 'cid' key
            result = response.json()
            if "cid" not in result:
                raise Exception(f"No CID returned: {result}")

            return result["cid"]

        except requests.exceptions.RequestException as e:
            raise Exception(f"Upload failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")
