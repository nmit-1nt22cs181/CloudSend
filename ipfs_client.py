# ipfs_client.py
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

class IPFSClient:
    def __init__(self):
        # Filebase IPFS API endpoint
        self.api_endpoint = "https://api.filebase.io/v1/ipfs/add"
        
        # Get API key from environment variable with hardcoded fallback
        self.api_key = os.getenv('FILEBASE_API_KEY', 'MTE5QTNFNjJDRkQ1NjA1NkMxMTk6N3U2cU5pNnAzU1h1ZjZhQVI2TEdIVXVZVjZKbEVQTXBtY3B3OFh6TTpjbG91ZC1zZW5kLXNhbmppdGg=')
        
        if not self.api_key:
            raise ValueError(
                "FILEBASE_API_KEY environment variable not set. "
                "Please set it with your Filebase API key."
            )
        
        # Setup session with retry logic for better reliability
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,  # Total number of retries
            backoff_factor=0.5,  # Wait 0.5, 1.0, 2.0 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('https://', adapter)

    def upload_file(self, file_path):
        """
        Upload a file to IPFS via Filebase API
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            str: IPFS CID (Content Identifier) of the uploaded file
            
        Raises:
            Exception: If upload fails
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                response = self.session.post(
                    self.api_endpoint, 
                    headers=headers, 
                    files=files,
                    timeout=30  # 30 second timeout
                )

            # Check for HTTP errors
            response.raise_for_status()

            # Filebase IPFS returns JSON with 'cid' key
            result = response.json()
            if "cid" not in result:
                raise Exception(f"No CID returned from Filebase: {result}")

            return result["cid"]

        except requests.exceptions.Timeout:
            raise Exception("Upload timed out after 30 seconds")
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error - check your internet connection")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP error during upload: {e.response.status_code} - {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Upload failed: {str(e)}")
        except FileNotFoundError:
            raise Exception(f"File not found: {file_path}")
        except Exception as e:
            raise Exception(f"Unexpected error during upload: {str(e)}")