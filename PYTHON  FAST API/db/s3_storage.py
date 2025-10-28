import boto3
import json
from typing import List, Optional
from config import settings
from modules.module import Document
from exception.exceptions import (
    S3UploadError,
    S3ListError,
    UnsupportedFileFormatError,
    DownloadError,
    S3FileNotFoundError
)

class S3Storage:

    def __init__(self, auto_create_bucket: bool = True):
        """
        Initialize S3 storage.
        """
        self.s3 = boto3.client('s3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION  
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        
        # Auto-create bucket if it doesn't exist
        if auto_create_bucket:
            self.ensure_bucket_exists()
      
    def ensure_bucket_exists(self) -> bool:
        """
        Ensure the S3 bucket exists. Create it if it doesn't.
        """
        try:
            # Check if bucket exists
            self.s3.head_bucket(Bucket=self.bucket_name)
            return True
        except self.s3.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    self.s3.create_bucket(Bucket=self.bucket_name)
                    return True
                except Exception as create_error:
                    print(f"Failed to create bucket: {create_error}")
                    return False
            else:
                return False
        except Exception as e:
            return False
    
    def create_document_s3(self, document: Document, format: str = "json") -> str:
        """
        Create a document in S3 with the specified format.
        """
        try:
            key = f"documents/{document.doc_id}"
            
            # Prepare content based on format
            if format.lower() == "json":
                content_dict = {
                    "doc_id": document.doc_id,
                    "doc_title": document.doc_title,
                    "description": document.description,
                    "content": document.content,
                    "doc_page_count": document.doc_page_count,
                    "isValid": document.isValid
                }
                
                body = json.dumps(content_dict, indent=2).encode("utf-8")   # converting as a json
                content_type = "application/json"
                
            elif format.lower() in ["text"]:
                # Store content as plain text
                body = document.content.encode("utf-8") if isinstance(document.content, str) else document.content
                content_type = "text/plain"
                                
            else:
                # Invalid format
                raise UnsupportedFileFormatError(
                    format=format,
                    supported_formats=['json', 'text'],
                    details={'requested_format': format.lower()}
                )
            
            # Add file extension to key based on format
            if format.lower() == "json":
                key = f"{key}.json"
            elif format.lower() in ["text"]:
                key = f"{key}.txt"
            
            # Upload to S3
            try:
                self.s3.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=body,
                    ContentType=content_type,
                    Metadata={
                        'doc_title': document.doc_title,
                        'format': format.lower()
                    }
                )
                return key
            except Exception as upload_error:
                raise S3UploadError(
                    s3_key=key,
                    reason=str(upload_error),
                    details={'bucket': self.bucket_name, 'format': format.lower()}
                )
            
        except Exception as e:
            raise S3UploadError(
            s3_key=f"documents/{document.doc_id}",
            reason=str(e),
            details={'format': format}
        )

    def list_all_files(self) -> List[dict]:
        """
        Retrieve all document file information from S3.
        """
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix="documents/")
                        
            if 'Contents' in response:
                files = []
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'file_type': obj['Key'].split('.')[-1] if '.' in obj['Key'] else None
                    })
                return files
            return []
            
        except Exception as e:
            raise S3ListError(
                prefix="documents/",
                reason=str(e),
                details={'bucket': self.bucket_name}
            )
    
    def get_file_content(self, key: str) -> dict:
        """
        Download and return the content of a specific file from S3.
        """
        try:
            file_obj = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            content = file_obj['Body'].read().decode('utf-8')
            file_type = key.split('.')[-1] if '.' in key else None  # finding the file type 
            
            return {
                'key': key,
                'content': content,
                'file_type': file_type
            }
        except Exception as e:
            raise DownloadError(
                prefix="documents/",
                reason=str(e),
                status_code=404,
                details={'bucket' : self.bucket_name}
            )
    
    def delete_file(self, key:str) -> bool:
        """
        Delete the file in s3
        """
        try:                    
            self.s3.delete_object(Bucket = self.bucket_name, Key = key) 
            return True
        except Exception as e:
            raise S3FileNotFoundError(
                s3_key=key,
                details={'bucket' : self.bucket_name}
            )
            
                    
    def update_document(self, document: Document, Key:str):
        
        try:
            self.s3.head_object(Bucket=self.bucket_name, Key= Key)
            format = "json" if Key.endswith(".json") else "text" 
            if format == "json":
                content_dict = {
                    "doc_id": document.doc_id,
                    "doc_title": document.doc_title,
                    "description": document.description,
                    "content": document.content,
                    "doc_page_count": document.doc_page_count,
                    "isValid": document.isValid
                }
                
                json_data = json.dumps(content_dict, indent=2).encode("utf-8")
                content_type = "application/json"
            else:
                json_data = document.content.encode("utf-8")
                content_type = "text/plain"
                    
            self.s3.put_object(
                Bucket = self.bucket_name,
                Key=Key,
                Body=json_data,
                ContentType=content_type,
                Metadata={
                    'doc_title': document.doc_title,
                    'format': format.lower()
                }
            )
            return Key 
        except Exception as e :
            raise S3FileNotFoundError(
                prefix="documents/",
                reason=str(e),
                details={'bucket': self.bucket_name}
            )
                
                
                
                
                
                        
            
            
                
                
                