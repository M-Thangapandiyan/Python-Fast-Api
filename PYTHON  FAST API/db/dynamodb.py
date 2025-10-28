import boto3
from typing import List

from botocore.exceptions import ClientError
from modules.module import Document
from config import settings


class DynamoDBDocumentStorage:

    def __init__(self):
        """Initialize the DynamoDBDocumentStorage."""
        self.dynamodb = boto3.resource('dynamodb', 
            endpoint_url=settings.LOCALSTACK_ENDPOINT_URL, 
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID, 
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.table = self.dynamodb.Table('document')

    def create_document(self, document: Document) -> Document:
        """Create a new document."""
        try:
            print(f"pydantic object{document}")
            print(f"document : == {document.model_dump()}")
            self.table.put_item(Item=document.model_dump())
            return document
        except ClientError as e:
            raise e


    def get_all_documents(self) -> List[Document]:
        """Return a list of all documents."""
        try:
            response = self.table.scan()
            documents = []
            for item in response['Items']:
                # Convert DynamoDB item to Document object
                # Use model_validate to handle field mapping properly
                document = Document.model_validate(item)
                documents.append(document)
            return documents 
        except ClientError as e:
            raise e
    
        
    def get_document_by_id(self, doc_id) -> Document | None:
        try:
            # Try to get from DynamoDB
            response = self.table.get_item(Key={"doc_id": doc_id})
            item = response.get("Item")
            
            if item:
                # Convert DynamoDB item to Document object
                return Document.model_validate(item)
            
            return None
            
        except ClientError as e:
            raise e
        
        
    def delete_document(self, doc_id: str) -> str:
        result = self.table.delete_item(
            Key = {"doc_id" : doc_id}, 
            ReturnValues="ALL_OLD"
        )
        return "Document deleted" if "Attributes" in result else "Document not found"
   
   
    def update_document(self, doc_id: str, document: Document) -> Document | None:
        try:
            # Update all fields of the document
            update_expression = (
                "SET doc_title = :title, "
                "description = :desc, "
                "content = :content, "
                "doc_page_count = :dpc, "
                "isValid = :valid"
               )
            expression_values = {
                ":title": document.doc_title,
                ":desc": document.description,
                ":content": document.content,
                ":dpc": document.doc_page_count,
                ":valid": document.isValid
            }
            
            result = self.table.update_item(
                Key={"doc_id": doc_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues="ALL_NEW"
            )
            updated_item = result.get("Attributes")
            if updated_item:
                return Document.model_validate(updated_item)
            return None
        except ClientError as e:
            raise e

