# Webmail API Specification for Flutter App

## Overview

RESTful API for Mushqila Webmail mobile application built with Flutter.

## Base URL

```
Production: https://mushqila.com/api/v1/webmail/
Development: http://localhost:8000/api/v1/webmail/
```

## Authentication

**Type**: Token-based authentication (JWT)

**Headers**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

---

## API Endpoints

### 1. Authentication

#### 1.1 Login
```
POST /api/v1/webmail/auth/login/
```

**Request Body**:
```json
{
  "email": "user@mushqila.com",
  "password": "SecurePass123"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
      "id": 1,
      "email": "user@mushqila.com",
      "first_name": "John",
      "last_name": "Doe",
      "display_name": "John Doe"
    },
    "account": {
      "id": 1,
      "email_address": "user@mushqila.com",
      "display_name": "John Doe",
      "mobile_number": "+8801712345678",
      "alternate_email": "john@gmail.com"
    }
  }
}
```

#### 1.2 Logout
```
POST /api/v1/webmail/auth/logout/
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

#### 1.3 Refresh Token
```
POST /api/v1/webmail/auth/refresh/
```

**Request Body**:
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

#### 1.4 Forgot Password
```
POST /api/v1/webmail/auth/forgot-password/
```

**Request Body**:
```json
{
  "email": "user@mushqila.com"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Temporary password sent to alternate email"
}
```

#### 1.5 Reset Password
```
POST /api/v1/webmail/auth/reset-password/
```

**Request Body**:
```json
{
  "email": "user@mushqila.com",
  "temporary_password": "aB3dE7fG",
  "new_password": "NewSecurePass123",
  "confirm_password": "NewSecurePass123"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Password reset successfully"
}
```

#### 1.6 Change Password
```
POST /api/v1/webmail/auth/change-password/
```

**Request Body**:
```json
{
  "current_password": "OldPass123",
  "new_password": "NewPass123",
  "confirm_password": "NewPass123"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

---

### 2. Emails

#### 2.1 Get Emails (Inbox/Folder)
```
GET /api/v1/webmail/emails/?folder=inbox&page=1&page_size=20
```

**Query Parameters**:
- `folder`: inbox, sent, drafts, trash, spam, archive, starred
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `is_read`: true/false (optional filter)
- `is_starred`: true/false (optional filter)

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "count": 150,
    "next": "https://mushqila.com/api/v1/webmail/emails/?page=2",
    "previous": null,
    "results": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "from_address": "sender@example.com",
        "from_name": "Sender Name",
        "to_addresses": ["user@mushqila.com"],
        "subject": "Meeting Tomorrow",
        "body_preview": "Hi, let's meet tomorrow at 10 AM...",
        "folder": "inbox",
        "is_read": false,
        "is_starred": false,
        "is_important": false,
        "has_attachments": true,
        "attachment_count": 2,
        "received_at": "2024-01-15T10:30:00Z",
        "size_bytes": 15360
      }
    ]
  }
}
```

#### 2.2 Get Email Detail
```
GET /api/v1/webmail/emails/{email_id}/
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "message_id": "<abc123@example.com>",
    "from_address": "sender@example.com",
    "from_name": "Sender Name",
    "to_addresses": ["user@mushqila.com"],
    "cc_addresses": ["cc@example.com"],
    "bcc_addresses": [],
    "reply_to": "sender@example.com",
    "subject": "Meeting Tomorrow",
    "body_text": "Hi, let's meet tomorrow at 10 AM...",
    "body_html": "<p>Hi, let's meet tomorrow at 10 AM...</p>",
    "folder": "inbox",
    "is_read": true,
    "is_starred": false,
    "is_important": false,
    "is_draft": false,
    "sent_at": null,
    "received_at": "2024-01-15T10:30:00Z",
    "read_at": "2024-01-15T11:00:00Z",
    "thread_id": "thread-123",
    "size_bytes": 15360,
    "attachments": [
      {
        "id": "att-001",
        "filename": "document.pdf",
        "content_type": "application/pdf",
        "size_bytes": 102400,
        "download_url": "https://mushqila.com/api/v1/webmail/attachments/att-001/download/"
      }
    ]
  }
}
```

#### 2.3 Send Email
```
POST /api/v1/webmail/emails/send/
```

**Request Body** (multipart/form-data):
```json
{
  "to_addresses": ["recipient@example.com"],
  "cc_addresses": ["cc@example.com"],
  "bcc_addresses": [],
  "subject": "Hello from Mobile",
  "body_text": "This is plain text body",
  "body_html": "<p>This is HTML body</p>",
  "attachments": [<file1>, <file2>]
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Email sent successfully",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "message_id": "<generated@mushqila.com>",
    "sent_at": "2024-01-15T12:00:00Z"
  }
}
```

#### 2.4 Save Draft
```
POST /api/v1/webmail/emails/draft/
```

**Request Body**:
```json
{
  "to_addresses": ["recipient@example.com"],
  "subject": "Draft Email",
  "body_text": "Draft content...",
  "body_html": "<p>Draft content...</p>"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Draft saved",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### 2.5 Mark as Read/Unread
```
PATCH /api/v1/webmail/emails/{email_id}/mark-read/
```

**Request Body**:
```json
{
  "is_read": true
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Email marked as read"
}
```

#### 2.6 Star/Unstar Email
```
PATCH /api/v1/webmail/emails/{email_id}/star/
```

**Request Body**:
```json
{
  "is_starred": true
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Email starred"
}
```

#### 2.7 Move to Folder
```
PATCH /api/v1/webmail/emails/{email_id}/move/
```

**Request Body**:
```json
{
  "folder": "trash"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Email moved to trash"
}
```

#### 2.8 Delete Email
```
DELETE /api/v1/webmail/emails/{email_id}/
```

**Query Parameters**:
- `permanent`: true/false (default: false)

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Email deleted"
}
```

#### 2.9 Search Emails
```
GET /api/v1/webmail/emails/search/?q=meeting&page=1
```

**Query Parameters**:
- `q`: Search query (required)
- `folder`: Filter by folder (optional)
- `from`: Filter by sender (optional)
- `date_from`: Filter by date (YYYY-MM-DD)
- `date_to`: Filter by date (YYYY-MM-DD)

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "count": 5,
    "results": [...]
  }
}
```

---

### 3. Attachments

#### 3.1 Download Attachment
```
GET /api/v1/webmail/attachments/{attachment_id}/download/
```

**Response**: File download (binary)

---

### 4. Contacts

#### 4.1 Get Contacts
```
GET /api/v1/webmail/contacts/?page=1&page_size=50
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "count": 100,
    "results": [
      {
        "id": 1,
        "email": "contact@example.com",
        "name": "Contact Name",
        "company": "Company Inc",
        "phone": "+1234567890",
        "is_favorite": false,
        "email_count": 15,
        "last_emailed": "2024-01-15T10:00:00Z"
      }
    ]
  }
}
```

#### 4.2 Create Contact
```
POST /api/v1/webmail/contacts/
```

**Request Body**:
```json
{
  "email": "new@example.com",
  "name": "New Contact",
  "company": "Company",
  "phone": "+1234567890",
  "notes": "Important client"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "email": "new@example.com",
    "name": "New Contact"
  }
}
```

#### 4.3 Update Contact
```
PUT /api/v1/webmail/contacts/{contact_id}/
```

#### 4.4 Delete Contact
```
DELETE /api/v1/webmail/contacts/{contact_id}/
```

---

### 5. Account Settings

#### 5.1 Get Account Info
```
GET /api/v1/webmail/account/
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "email_address": "user@mushqila.com",
    "display_name": "John Doe",
    "first_name": "John",
    "last_name": "Doe",
    "mobile_number": "+8801712345678",
    "alternate_email": "john@gmail.com",
    "signature": "Best regards,\nJohn Doe",
    "is_active": true,
    "ses_verified": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### 5.2 Update Account
```
PATCH /api/v1/webmail/account/
```

**Request Body**:
```json
{
  "display_name": "John M. Doe",
  "mobile_number": "+8801712345678",
  "signature": "Best regards,\nJohn M. Doe"
}
```

---

### 6. Statistics

#### 6.1 Get Email Stats
```
GET /api/v1/webmail/stats/
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "total_emails": 500,
    "unread_count": 25,
    "inbox_count": 150,
    "sent_count": 200,
    "drafts_count": 5,
    "trash_count": 10,
    "spam_count": 3,
    "starred_count": 20,
    "storage_used_bytes": 52428800,
    "storage_used_mb": 50
  }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "email": ["This field is required"],
      "password": ["Password must be at least 8 characters"]
    }
  }
}
```

### 401 Unauthorized
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication credentials were not provided"
  }
}
```

### 403 Forbidden
```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have permission to perform this action"
  }
}
```

### 404 Not Found
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Email not found"
  }
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred"
  }
}
```

---

## Rate Limiting

- **Authentication endpoints**: 5 requests per minute
- **Email sending**: 10 requests per minute
- **Other endpoints**: 60 requests per minute

**Rate Limit Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642248000
```

---

## Pagination

All list endpoints support pagination:

**Query Parameters**:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

**Response Format**:
```json
{
  "count": 150,
  "next": "https://mushqila.com/api/v1/webmail/emails/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Filtering & Sorting

**Filtering**:
```
GET /api/v1/webmail/emails/?folder=inbox&is_read=false&is_starred=true
```

**Sorting**:
```
GET /api/v1/webmail/emails/?ordering=-received_at
GET /api/v1/webmail/emails/?ordering=subject
```

Available sort fields:
- `received_at`, `-received_at`
- `subject`, `-subject`
- `from_address`, `-from_address`
- `size_bytes`, `-size_bytes`

---

## Webhooks (Optional)

### Email Received Webhook
```
POST <your_webhook_url>
```

**Payload**:
```json
{
  "event": "email.received",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "email_id": "550e8400-e29b-41d4-a716-446655440000",
    "from": "sender@example.com",
    "subject": "New Email",
    "received_at": "2024-01-15T10:30:00Z"
  }
}
```

---

## Testing

### Postman Collection
Available at: `/api/v1/webmail/docs/postman/`

### Swagger/OpenAPI
Available at: `/api/v1/webmail/docs/swagger/`

### API Playground
Available at: `/api/v1/webmail/docs/playground/`
