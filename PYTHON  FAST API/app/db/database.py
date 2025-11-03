"""
DynamoDB database.
"""

from typing import List, Optional
from botocore.exceptions import ClientError
from app.schemas.document import Document
from app.schemas.user import User
from app.utils.logger import logger
from app.db.dynamodb import get_document_table, get_user_table


document_table = get_document_table()
user_table = get_user_table()


def create_document(document: Document) -> Document:
        """Create a new document."""
        try:
            logger.info(f"pydantic object{document}")
            logger.info(f"document  {document.model_dump()}")
            document_table.put_item(Item=document.model_dump())
            return document
        except ClientError as e:
            raise e

def get_all_documents() -> List[Document]:
        """Return a list of all documents."""
        try:
            response = document_table.scan()
            documents = []
            for item in response['Items']:
                # Convert DynamoDB item to Document object
                # Use model_validate to handle field mapping properly
                document = Document.model_validate(item)
                documents.append(document)
            return documents 
        except ClientError as e:
            raise e
    
def get_document_by_id(doc_id) -> Optional[Document]:
        try:
            # Try to get from DynamoDB
            response = document_table.get_item(Key={"doc_id": doc_id})
            item = response.get("Item")
            if item:
                return Document.model_validate(item)
            return None
            
        except ClientError as e:
            raise e
        
def delete_document(doc_id: str) -> str:
        result = document_table.delete_item(
            Key = {"doc_id" : doc_id}, 
            ReturnValues="ALL_OLD"
        )
        return True if "Attributes" in result else False
    
def update_document(doc_id: str, document: Document) -> Optional[Document]:
        try:
            update_expression = (
                "SET doc_title = :title, "
                "description = :desc, "
                "content = :content, "
                "doc_page_count = :dpc, "
                "is_valid = :valid"
               )
            expression_values = {
                ":title": document.doc_title,
                ":desc": document.description,
                ":content": document.content,
                ":dpc": document.doc_page_count,
                ":valid": document.is_valid
            }
            
            result = document_table.update_item(
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

def create_user(user: User):
        """Create a new user record."""
        try:
            logger.info(f"User dump: {user.model_dump()}")
            user_table.put_item(Item=user.model_dump())
            return {"message": "User created successfully"}
        except ClientError as e:
            raise e


def get_user(username: str = None, email: str = None):
    """Fetch user by username or email."""
    try:
        if username:
            response = user_table.get_item(Key={"user_name": username})
            return response.get("Item")
        elif email:
            response = user_table.scan(
            FilterExpression="email = :email",
            ExpressionAttributeValues={":email": email}
            )
            items = response.get("Items", [])
            if items:
                return items[0]
        return None
    except ClientError as e:
        raise e


 
def get_all_user():
        """Fetch users """
        try:
            response = user_table.scan()
            users = [user for user in response["Items"]]
            return users
        except ClientError as e:
            raise e


def delete_user(username: str) -> bool:
    """Delete a user by username."""
    try:
        result = user_table.delete_item(
            Key={"user_name": username},
            ReturnValues="ALL_OLD"
        )
        return True if "Attributes" in result else False
    except ClientError as e:
        raise e


def update_user(username: str, user_update: dict) -> Optional[dict]:
    """Update user by username."""
    try:
        # Build update expression dynamically based on provided fields
        update_parts = []
        expression_values = {}
        expression_names = {}
        
        if "email" in user_update and user_update["email"] is not None:
            update_parts.append("email = :email")
            expression_values[":email"] = user_update["email"]
        
        if "password" in user_update and user_update["password"] is not None:
            update_parts.append("password = :password")
            expression_values[":password"] = user_update["password"]
        
        if "is_active" in user_update and user_update["is_active"] is not None:
            update_parts.append("#is_active = :is_active")
            expression_values[":is_active"] = user_update["is_active"]
            expression_names["#is_active"] = "is_active"  # Reserved word handling
        
        
        update_expression = f"SET {', '.join(update_parts)}"
        
        update_params = {
            "Key": {"user_name": username},
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expression_values,
            "ReturnValues": "ALL_NEW"
        }
        
        if expression_names:
            update_params["ExpressionAttributeNames"] = expression_names
        
        result = user_table.update_item(**update_params)
        updated_item = result.get("Attributes")
        return updated_item if updated_item else None
    except ClientError as e:
        raise e