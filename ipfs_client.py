# ipfs_client.py - S3 Compatible API Version with Download Support
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import os
import requests
import logging

logger = logging.getLogger(__name__)


class IPFSClient:
    def __init__(self):
        # Get credentials from environment variables with hardcoded fallback
        access_key = os.getenv("FILEBASE_ACCESS_KEY", "119A3E62CFD56056C119")
        secret_key = os.getenv(
            "FILEBASE_SECRET_KEY", "7u6qNi6p3SXuf6aAR6LGHUuYV6JlEPMpmcpw8XzM"
        )

        # Bucket name - REPLACE 'cloudsend-uploads' with YOUR actual bucket name from Filebase!
        self.bucket_name = os.getenv("FILEBASE_BUCKET", "cloud-send-sanjith")

        if not access_key:
            raise ValueError(
                "FILEBASE_ACCESS_KEY environment variable not set. "
                "Please set it with your Filebase Access Key ID."
            )

        if not secret_key:
            raise ValueError(
                "FILEBASE_SECRET_KEY environment variable not set. "
                "Please set it with your Filebase Secret Access Key."
            )

        # Initialize S3 client with Filebase endpoint
        self.s3_client = boto3.client(
            "s3",
            endpoint_url="https://s3.filebase.com",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",  # Filebase uses us-east-1
        )

    def upload_file(self, file_path):
        """
        Upload a file to IPFS via Filebase S3 API

        Args:
            file_path: Path to the file to upload

        Returns:
            str: IPFS CID (Content Identifier) of the uploaded file

        Raises:
            Exception: If upload fails
        """
        try:
            # Get just the filename for the S3 key
            filename = os.path.basename(file_path)

            # Upload file to Filebase bucket
            self.s3_client.upload_file(file_path, self.bucket_name, filename)

            # Get the CID from the file metadata
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=filename)

            # Filebase returns the CID in the metadata
            cid = response.get("Metadata", {}).get("cid")

            if not cid:
                # Fallback: try to get it from custom headers
                cid = (
                    response.get("ResponseMetadata", {})
                    .get("HTTPHeaders", {})
                    .get("x-amz-meta-cid")
                )

            if not cid:
                raise Exception("No CID returned from Filebase after upload")

            return cid

        except FileNotFoundError:
            raise Exception(f"File not found: {file_path}")
        except NoCredentialsError:
            raise Exception("Invalid Filebase credentials")
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]

            if error_code == "NoSuchBucket":
                raise Exception(
                    f"Bucket '{self.bucket_name}' does not exist. Please create it in Filebase first."
                )
            elif error_code == "AccessDenied":
                raise Exception(
                    "Access denied. Check your Filebase credentials and bucket permissions."
                )
            else:
                raise Exception(f"S3 error: {error_code} - {error_message}")
        except Exception as e:
            raise Exception(f"Upload failed: {str(e)}")

    def download_file(self, ipfs_hash):
        """
        Download a file from IPFS using the CID

        Args:
            ipfs_hash: IPFS CID (Content Identifier) of the file

        Returns:
            bytes: File content

        Raises:
            Exception: If download fails
        """
        try:
            # Method 1: Try to download directly from Filebase using the CID as key
            # First, try to find the file by listing objects and matching CID
            try:
                logger.info(f"Attempting to download file with CID: {ipfs_hash}")

                # List all objects in the bucket
                response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)

                if "Contents" in response:
                    for obj in response["Contents"]:
                        # Get metadata for each object
                        head_response = self.s3_client.head_object(
                            Bucket=self.bucket_name, Key=obj["Key"]
                        )

                        # Check if this object's CID matches
                        obj_cid = head_response.get("Metadata", {}).get("cid")
                        if not obj_cid:
                            obj_cid = (
                                head_response.get("ResponseMetadata", {})
                                .get("HTTPHeaders", {})
                                .get("x-amz-meta-cid")
                            )

                        if obj_cid == ipfs_hash:
                            # Found the matching file, download it
                            logger.info(f"Found matching file: {obj['Key']}")
                            file_obj = self.s3_client.get_object(
                                Bucket=self.bucket_name, Key=obj["Key"]
                            )
                            return file_obj["Body"].read()

                logger.warning(
                    f"File with CID {ipfs_hash} not found in Filebase bucket"
                )

            except ClientError as e:
                logger.warning(f"Error accessing Filebase bucket: {e}")

            # Method 2: Try public IPFS gateways
            logger.info(f"Attempting to download from public IPFS gateways")
            gateways = [
                f"https://ipfs.filebase.io/ipfs/{ipfs_hash}",
                f"https://ipfs.io/ipfs/{ipfs_hash}",
                f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}",
                f"https://cloudflare-ipfs.com/ipfs/{ipfs_hash}",
            ]

            for gateway_url in gateways:
                try:
                    logger.info(f"Trying gateway: {gateway_url}")
                    response = requests.get(gateway_url, timeout=30)
                    if response.status_code == 200:
                        logger.info(
                            f"Successfully downloaded from gateway: {gateway_url}"
                        )
                        return response.content
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Gateway {gateway_url} failed: {e}")
                    continue

            raise Exception(
                f"Failed to download file with CID {ipfs_hash} from any source"
            )

        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            raise Exception(f"Download failed: {str(e)}")

    def get_file_info(self, ipfs_hash):
        """
        Get information about a file stored in IPFS

        Args:
            ipfs_hash: IPFS CID of the file

        Returns:
            dict: File information including size, content type, etc.
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)

            if "Contents" in response:
                for obj in response["Contents"]:
                    head_response = self.s3_client.head_object(
                        Bucket=self.bucket_name, Key=obj["Key"]
                    )

                    obj_cid = head_response.get("Metadata", {}).get("cid")
                    if not obj_cid:
                        obj_cid = (
                            head_response.get("ResponseMetadata", {})
                            .get("HTTPHeaders", {})
                            .get("x-amz-meta-cid")
                        )

                    if obj_cid == ipfs_hash:
                        return {
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "last_modified": obj["LastModified"],
                            "cid": obj_cid,
                        }

            return None

        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None