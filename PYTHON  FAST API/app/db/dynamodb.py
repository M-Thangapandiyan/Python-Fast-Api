"""
DynamoDB database implementation.
"""
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
from app.utils.logger import logger

dynamodb = boto3.resource(
    'dynamodb', 
    endpoint_url=settings.LOCALSTACK_ENDPOINT_URL, 
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID, 
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)
       
       
def ensure_table_exists(table_name: str, key_schema, attribute_definitions):
    """Create table if it doesn't exist"""
    try:
        table = dynamodb.Table(table_name)
        table.load()  # Triggers ResourceNotFoundException if missing
        print(f"Table '{table_name}' already exists.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"Creating DynamoDB table: {table_name}")
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=key_schema,
                AttributeDefinitions=attribute_definitions,
                BillingMode="PAY_PER_REQUEST"
            )
            table.wait_until_exists()
            print(f"Table '{table_name}' created successfully.")
    return dynamodb.Table(table_name)       
              
       
def get_document_table():
    return ensure_table_exists(
        "document",
        key_schema=[{"AttributeName": "doc_id", "KeyType": "HASH"}],
        attribute_definitions=[{"AttributeName": "doc_id", "AttributeType": "S"}]
    )
        
        
def get_user_table():
    return ensure_table_exists(
        "users",
        key_schema=[{"AttributeName": "user_name", "KeyType": "HASH"}],
        attribute_definitions=[{"AttributeName": "user_name", "AttributeType": "S"}]
    )
        
            
# s3 bucket setup          
s3 = boto3.client('s3',
    endpoint_url=settings.S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.S3_REGION  
)

      
bucket_name = settings.S3_BUCKET_NAME

            
def ensure_bucket_exists() -> str:
    """
    Ensure the S3 bucket exists. Create it if it doesn't.
    """
    try:
        # Check if bucket exists
        s3.head_bucket(Bucket=bucket_name)
        return bucket_name
    except s3.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
        # Bucket doesn't exist, create it
            try:
                s3.create_bucket(Bucket=bucket_name)
                return bucket_name
            except Exception as error:
                raise error
        else:
            return False
    except Exception as e:
        return False        
    

def get_bucket():     
    return s3

