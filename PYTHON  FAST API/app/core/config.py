from dotenv import load_dotenv
import os

# Load .env file from the project root
load_dotenv()


class Settings:
    # Application Configuration
    APP_NAME: str = os.getenv("APP_NAME", "FastAPI Document Service")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    LOCALSTACK_ENDPOINT_URL: str = os.getenv("LOCALSTACK_ENDPOINT_URL", "http://localhost:4566")
   
    
    # S3 Configuration
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "http://localhost:4566")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "documents-bucket")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
    
    # Database Configuration - DynamoDB
    DYNAMODB_TABLE_NAME: str = os.getenv("DYNAMODB_TABLE_NAME", "documents")
    DYNAMODB_REGION: str = os.getenv("DYNAMODB_REGION", "us-east-1")

    # AWS Credentials (LocalStack/local development)
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "test")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
    AWS_DEFAULT_REGION: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

    # API Configuration
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")
    DOCS_URL: str = os.getenv("DOCS_URL", "/docs")
    APPLICATION_TAG: str = os.getenv("APPLICATION_TAG", "documents")

    # Health Check Configuration
    HEALTH_CHECK_ENDPOINT: str = os.getenv("HEALTH_CHECK_ENDPOINT", "/health")

    # JWT Authentication Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    JWT_ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_HOURS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_HOURS", "24"))



settings = Settings()

