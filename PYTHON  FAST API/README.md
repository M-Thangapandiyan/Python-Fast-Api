# FastAPI Document Service

A FastAPI-based document management service with DynamoDB and S3 integration, featuring JWT authentication.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start LocalStack (for local development)
docker run -d -p 4566:4566 -p 4571:4571 localstack/localstack

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access API documentation at: **http://localhost:8000/docs**

## API Endpoints

### Authentication
- `POST /login` - Login and get access/refresh tokens
- `POST /refresh` - Refresh access token

### Documents (Auth Required)
- `POST /api/v1/documents/` - Create document (`?format=json|text`)
- `GET /api/v1/documents/` - List all documents
- `GET /api/v1/documents/{doc_id}` - Get document by ID
- `PATCH /api/v1/documents/{doc_id}` - Update document
- `DELETE /api/v1/documents/{doc_id}` - Delete document

### Users
- `POST /api/v1/user/` - Create user (public)
- `GET /api/v1/user/` - Get user by username/email (Auth Required)
- `GET /api/v1/users/` - List all users (Auth Required)
- `PATCH /api/v1/user/{username}` - Update user (Auth Required)
- `DELETE /api/v1/user/{username}` - Delete user (Auth Required)

### Utility
- `GET /` - API information
- `GET /health` - Health check

## Authentication

The API uses JWT tokens. Login to get tokens, then use in the Authorization header:

```
Authorization: Bearer <access_token>
```
