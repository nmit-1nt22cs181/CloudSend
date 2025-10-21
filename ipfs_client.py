# ipfs_client.py - S3 Compatible API Version
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import os

class IPFSClient:
    def __init__(self):
        # Get credentials from environment variables with hardcoded fallback
        access_key = os.getenv('FILEBASE_ACCESS_KEY', '119A3E62CFD56056C119')
        secret_key = os.getenv('FILEBASE_SECRET_KEY', '7u6qNi6p3SXuf6aAR6LGHUuYV6JlEPMpmcpw8XzM')
        
        # Bucket name - REPLACE 'cloudsend-uploads' with YOUR actual bucket name from Filebase!
        self.bucket_name = os.getenv('FILEBASE_BUCKET', 'cloud-send-sanjith')
        
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
            's3',
            endpoint_url='https://s3.filebase.com',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='us-east-1'  # Filebase uses us-east-1
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
            cid = response.get('Metadata', {}).get('cid')
            
            if not cid:
                # Fallback: try to get it from custom headers
                cid = response.get('ResponseMetadata', {}).get('HTTPHeaders', {}).get('x-amz-meta-cid')
            
            if not cid:
                raise Exception("No CID returned from Filebase after upload")
            
            return cid
            
        except FileNotFoundError:
            raise Exception(f"File not found: {file_path}")
        except NoCredentialsError:
            raise Exception("Invalid Filebase credentials")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'NoSuchBucket':
                raise Exception(f"Bucket '{self.bucket_name}' does not exist. Please create it in Filebase first.")
            elif error_code == 'AccessDenied':
                raise Exception("Access denied. Check your Filebase credentials and bucket permissions.")
            else:
                raise Exception(f"S3 error: {error_code} - {error_message}")
        except Exception as e:
            raise Exception(f"Upload failed: {str(e)}")