# Webmail API - সম্পূর্ণ Endpoint তালিকা (Flutter App এর জন্য)

## 📱 API Base URL
```
Production: https://mushqila.com/api/v1/webmail
Local: http://localhost:8000/api/v1/webmail
```

---

## 🔐 Authentication Endpoints (৬টি)

### 1. Login (লগইন)
```
POST /auth/login/
```

**Request Body:**
```json
{
  "email": "user@mushqila.com",
  "password": "password123"
}
```

**Response (Success):**
```json
{
  "success": true,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
      "id": 1,
      "username": "user",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe"
    },
    "account": {
      "id": 1,
      "email_address": "user@mushqila.com",
      "display_name": "John Doe",
      "first_name": "John",
      "last_name": "Doe",
      "mobile_number": "+8801712345678",
      "alternate_email": "john@gmail.com",
      "is_active": true,
      "ses_verified": true
    }
  }
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password"
  }
}
```

---

### 2. Logout (লগআউট)
```
POST /auth/logout/
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

### 3. Token Refresh (টোকেন রিফ্রেশ)
```
POST /auth/refresh/
```

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### 4. Forgot Password (পাসওয়ার্ড ভুলে গেছেন)
```
POST /auth/forgot-password/
```

**Request Body:**
```json
{
  "email": "user@mushqila.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Temporary password sent to alternate email"
}
```

---

### 5. Reset Password (পাসওয়ার্ড রিসেট)
```
POST /auth/reset-password/
```

**Request Body:**
```json
{
  "email": "user@mushqila.com",
  "temporary_password": "temp123456",
  "new_password": "newpass123",
  "confirm_password": "newpass123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Password reset successfully"
}
```

---

### 6. Change Password (পাসওয়ার্ড পরিবর্তন)
```
POST /auth/change-password/
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "current_password": "oldpass123",
  "new_password": "newpass123",
  "confirm_password": "newpass123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

---

## 📧 Email Endpoints (৯টি)

### 7. Get Emails List (ইমেইল তালিকা)
```
GET /emails/?folder=inbox&page=1&page_size=20
Authorization: Bearer {token}
```

**Query Parameters:**
- `folder`: inbox, sent, drafts, trash, spam (default: inbox)
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)
- `is_read`: true/false (optional)
- `is_starred`: true/false (optional)
- `ordering`: -received_at, received_at, subject (default: -received_at)

**Response:**
```json
{
  "success": true,
  "data": {
    "count": 150,
    "next": "http://localhost:8000/api/v1/webmail/emails/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "from_address": "sender@example.com",
        "from_name": "Sender Name",
        "to_addresses": ["user@mushqila.com"],
        "subject": "Meeting Tomorrow",
        "body_preview": "Hi, I wanted to confirm our meeting...",
        "folder": "inbox",
        "is_read": false,
        "is_starred": false,
        "is_important": false,
        "has_attachments": true,
        "attachment_count": 2,
        "received_at": "2026-04-19T10:30:00Z",
        "size_bytes": 15420
      }
    ]
  }
}
```

---

### 8. Get Email Detail (ইমেইল বিস্তারিত)
```
GET /emails/{id}/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "message_id": "<abc123@mushqila.com>",
    "from_address": "sender@example.com",
    "from_name": "Sender Name",
    "to_addresses": ["user@mushqila.com"],
    "cc_addresses": ["cc@example.com"],
    "bcc_addresses": [],
    "reply_to": "reply@example.com",
    "subject": "Meeting Tomorrow",
    "body_text": "Hi, I wanted to confirm our meeting...",
    "body_html": "<p>Hi, I wanted to confirm our meeting...</p>",
    "folder": "inbox",
    "is_read": true,
    "is_starred": false,
    "is_important": false,
    "is_draft": false,
    "sent_at": null,
    "received_at": "2026-04-19T10:30:00Z",
    "read_at": "2026-04-19T11:00:00Z",
    "thread_id": null,
    "size_bytes": 15420,
    "attachments": [
      {
        "id": 1,
        "filename": "document.pdf",
        "content_type": "application/pdf",
        "size_bytes": 102400,
        "is_inline": false,
        "download_url": "http://localhost:8000/api/v1/webmail/attachments/1/download/"
      }
    ]
  }
}
```

---

### 9. Send Email (ইমেইল পাঠান)
```
POST /emails/send/
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "to_addresses": ["recipient@example.com"],
  "cc_addresses": ["cc@example.com"],
  "bcc_addresses": ["bcc@example.com"],
  "subject": "Test Email",
  "body_text": "This is the plain text version",
  "body_html": "<p>This is the <strong>HTML</strong> version</p>"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email sent successfully",
  "data": {
    "id": 123,
    "message_id": "<xyz789@mushqila.com>"
  }
}
```

---

### 10. Save Draft (ড্রাফট সংরক্ষণ)
```
POST /emails/draft/
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "to_addresses": ["recipient@example.com"],
  "cc_addresses": [],
  "subject": "Draft Email",
  "body_text": "This is a draft...",
  "body_html": "<p>This is a draft...</p>"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Draft saved",
  "data": {
    "id": 124
  }
}
```

---

### 11. Mark as Read/Unread (পঠিত/অপঠিত চিহ্নিত করুন)
```
PATCH /emails/{id}/mark_read/
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "is_read": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email marked as read"
}
```

---

### 12. Star/Unstar Email (তারকা চিহ্ন)
```
PATCH /emails/{id}/star/
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "is_starred": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email starred"
}
```

---

### 13. Move to Folder (ফোল্ডারে সরান)
```
PATCH /emails/{id}/move/
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "folder": "trash"
}
```

**Valid folders:** inbox, sent, drafts, trash, spam

**Response:**
```json
{
  "success": true,
  "message": "Email moved to trash"
}
```

---

### 14. Delete Email (ইমেইল মুছুন)
```
DELETE /emails/{id}/?permanent=false
Authorization: Bearer {token}
```

**Query Parameters:**
- `permanent`: true (স্থায়ীভাবে মুছুন), false (ট্র্যাশে সরান)

**Response:**
```json
{
  "success": true,
  "message": "Email moved to trash"
}
```

---

### 15. Search Emails (ইমেইল খুঁজুন)
```
GET /emails/search/?q=meeting&folder=inbox&from=sender@example.com
Authorization: Bearer {token}
```

**Query Parameters:**
- `q`: Search query (required)
- `folder`: Filter by folder (optional)
- `from`: Filter by sender (optional)
- `page`: Page number
- `page_size`: Items per page

**Response:**
```json
{
  "success": true,
  "data": {
    "count": 5,
    "results": [
      {
        "id": 1,
        "from_address": "sender@example.com",
        "subject": "Meeting Tomorrow",
        "body_preview": "Hi, I wanted to confirm our meeting...",
        "folder": "inbox",
        "is_read": false,
        "received_at": "2026-04-19T10:30:00Z"
      }
    ]
  }
}
```

---

## 👥 Contact Endpoints (৫টি)

### 16. Get Contacts List (যোগাযোগ তালিকা)
```
GET /contacts/?page=1
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "count": 50,
    "results": [
      {
        "id": 1,
        "email": "contact@example.com",
        "name": "John Doe",
        "company": "ABC Corp",
        "phone": "+8801712345678",
        "notes": "Important client",
        "is_favorite": true,
        "email_count": 25,
        "last_emailed": "2026-04-19T10:30:00Z",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-04-19T10:30:00Z"
      }
    ]
  }
}
```

---

### 17. Get Contact Detail (যোগাযোগ বিস্তারিত)
```
GET /contacts/{id}/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "email": "contact@example.com",
    "name": "John Doe",
    "company": "ABC Corp",
    "phone": "+8801712345678",
    "notes": "Important client",
    "is_favorite": true,
    "email_count": 25,
    "last_emailed": "2026-04-19T10:30:00Z"
  }
}
```

---

### 18. Create Contact (যোগাযোগ তৈরি করুন)
```
POST /contacts/
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "email": "newcontact@example.com",
  "name": "Jane Smith",
  "company": "XYZ Ltd",
  "phone": "+8801798765432",
  "notes": "Met at conference",
  "is_favorite": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "email": "newcontact@example.com",
    "name": "Jane Smith",
    "company": "XYZ Ltd",
    "phone": "+8801798765432",
    "notes": "Met at conference",
    "is_favorite": false,
    "email_count": 0,
    "last_emailed": null
  }
}
```

---

### 19. Update Contact (যোগাযোগ আপডেট করুন)
```
PATCH /contacts/{id}/
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "name": "Jane Smith Updated",
  "is_favorite": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "email": "newcontact@example.com",
    "name": "Jane Smith Updated",
    "is_favorite": true
  }
}
```

---

### 20. Delete Contact (যোগাযোগ মুছুন)
```
DELETE /contacts/{id}/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "message": "Contact deleted"
}
```

---

## 👤 Account Endpoints (২টি)

### 21. Get Account Info (অ্যাকাউন্ট তথ্য)
```
GET /account/
Authorization: Bearer {token}
```

**Response:**
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
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-04-19T10:30:00Z"
  }
}
```

---

### 22. Update Account (অ্যাকাউন্ট আপডেট)
```
PATCH /account/update/
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "display_name": "John M. Doe",
  "mobile_number": "+8801712345679",
  "signature": "Best regards,\nJohn M. Doe\nSenior Manager"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "email_address": "user@mushqila.com",
    "display_name": "John M. Doe",
    "mobile_number": "+8801712345679",
    "signature": "Best regards,\nJohn M. Doe\nSenior Manager"
  }
}
```

---

## 📊 Statistics Endpoint (১টি)

### 23. Get Email Statistics (ইমেইল পরিসংখ্যান)
```
GET /stats/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_emails": 500,
    "unread_count": 45,
    "inbox_count": 150,
    "sent_count": 200,
    "drafts_count": 10,
    "trash_count": 30,
    "spam_count": 5,
    "starred_count": 25,
    "storage_used_bytes": 52428800,
    "storage_used_mb": 50.0
  }
}
```

---

## 📎 Attachment Endpoint (১টি)

### 24. Download Attachment (সংযুক্তি ডাউনলোড)
```
GET /attachments/{attachment_id}/download/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "download_url": "https://s3.amazonaws.com/mushqila-inbox/...",
    "filename": "document.pdf",
    "content_type": "application/pdf",
    "size_bytes": 102400
  }
}
```

---

## 🔒 Security & Authentication

### JWT Token
- Access Token Lifetime: 1 hour
- Refresh Token Lifetime: 7 days
- Token Type: Bearer
- Header Format: `Authorization: Bearer {token}`

### Token Refresh Strategy
```dart
// Flutter example
if (response.statusCode == 401) {
  // Token expired, refresh it
  await refreshToken();
  // Retry the request
}
```

---

## ⚠️ Error Codes

| Code | Message | HTTP Status |
|------|---------|-------------|
| VALIDATION_ERROR | Invalid input data | 400 |
| INVALID_CREDENTIALS | Invalid email or password | 401 |
| UNAUTHORIZED | Authentication required | 401 |
| FORBIDDEN | Permission denied | 403 |
| NOT_FOUND | Resource not found | 404 |
| NO_ACCOUNT | No email account found | 404 |
| NO_ALTERNATE_EMAIL | No alternate email found | 400 |
| INVALID_TOKEN | Invalid or expired token | 400 |
| INVALID_PASSWORD | Current password incorrect | 400 |
| INVALID_FOLDER | Invalid folder name | 400 |
| MISSING_QUERY | Search query required | 400 |
| SEND_ERROR | Failed to send email | 500 |
| DRAFT_ERROR | Failed to save draft | 500 |
| LOGOUT_ERROR | Logout failed | 400 |

---

## 📱 Flutter Integration Quick Start

### 1. Dependencies (pubspec.yaml)
```yaml
dependencies:
  http: ^1.1.0
  shared_preferences: ^2.2.2
  flutter_secure_storage: ^9.0.0
```

### 2. API Service Class
```dart
class WebmailAPI {
  static const baseUrl = 'https://mushqila.com/api/v1/webmail';
  
  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    return jsonDecode(response.body);
  }
  
  Future<Map<String, dynamic>> getEmails({String folder = 'inbox'}) async {
    final token = await getToken();
    final response = await http.get(
      Uri.parse('$baseUrl/emails/?folder=$folder'),
      headers: {'Authorization': 'Bearer $token'},
    );
    return jsonDecode(response.body);
  }
}
```

---

## ✅ API Status: 100% Complete

**Total Endpoints: 24**
- Authentication: 6
- Email Operations: 9
- Contacts: 5
- Account: 2
- Statistics: 1
- Attachments: 1

**সবকিছু Flutter mobile app এর জন্য প্রস্তুত!**

---

**তৈরি করেছেন:** Mushqila Development Team  
**তারিখ:** ১৯ এপ্রিল, ২০২৬  
**সংস্করণ:** 1.0  
**স্ট্যাটাস:** Production Ready ✅
