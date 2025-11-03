"""
S3 storage implementation for document/file storage.
"""

import json
from typing import List
from app.schemas.document import Document
from app.db.dynamodb import (
    ensure_bucket_exists, 
    get_bucket
)

from app.core.exceptions import (
    S3UploadError,
    S3ListError,
    UnsupportedFileFormatError,
    DownloadError,
    S3FileNotFoundError
)
from app.utils.logger import logger

bucket_name = ensure_bucket_exists()    
s3_client = get_bucket()   
    
            
def create_document_s3(document: Document, format: str = "json") -> str:
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
                    "is_valid": document.is_valid
                }
                
                body = json.dumps(content_dict, indent=2).encode("utf-8")  
                content_type = "application/json"
                
            elif format.lower() in ["text"]:
                body = document.content.encode("utf-8") if isinstance(
                    document.content, str
                ) else document.content
                content_type = "text/plain"
                                
            else:
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
                s3_client.put_object(
                    Bucket=bucket_name,
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
                    details={'bucket': bucket_name, 'format': format.lower()}
                )
            
        except Exception as e:
            raise S3UploadError(
            s3_key=f"documents/{document.doc_id}",
            reason=str(e),
            details={'format': format}
        )

def list_all_files() -> List[dict]:
        """
        Retrieve all document file information from S3.
        """
        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix="documents/"
            )
                        
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
                details={'bucket': bucket_name}
            )
    
def get_file_content(key: str) -> dict:
        """
        Download and return the content of a specific file from S3.
        """
        try:
            file_obj = s3_client.get_object(Bucket=bucket_name, Key=key)
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
                details={'bucket' : bucket_name}
            )
    
def delete_file_s3(key: str) -> bool:
        """
        Delete the file in s3
        """
        try:                    
            s3_client.delete_object(Bucket=bucket_name, Key=key) 
            return True
        except Exception as e:
            raise S3FileNotFoundError(
                s3_key=key,
                details={'bucket' : bucket_name}
            )
                    
def update_document_s3(document: Document, Key: str):
        try:
            s3_client.head_object(Bucket=bucket_name, Key=Key)
            format = "json" if Key.endswith(".json") else "text" 
            if format == "json":
                content_dict = {
                    "doc_id": document.doc_id,
                    "doc_title": document.doc_title,
                    "description": document.description,
                    "content": document.content,
                    "doc_page_count": document.doc_page_count,
                    "is_valid": document.is_valid
                }
                
                json_data = json.dumps(content_dict, indent=2).encode("utf-8")
                content_type = "application/json"
            else:
                json_data = document.content.encode("utf-8")
                content_type = "text/plain"
                    
            s3_client.put_object(
                Bucket=bucket_name,
                Key=Key,
                Body=json_data,
                ContentType=content_type,
                Metadata={
                    'doc_title': document.doc_title,
                    'format': format.lower()
                }
            )
            return Key 
        except Exception as e:
            raise S3FileNotFoundError(
                s3_key=Key,
                 details={'bucket': bucket_name,  "reason" : str(e)}
            )

