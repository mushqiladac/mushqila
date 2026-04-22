# Webmail API Testing Guide

## Setup

### 1. Install Dependencies

```bash
pip install djangorestframework-simplejwt==5.3.0
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Create Test Email Account

```bash
python manage.py create_webmail_account \
  --email test@mushqila.com \
  --password TestPass123 \
  --first-name "Test" \
  --last-name "User" \
  --alternate-email "test.user@gmail.com"
```

---

## API Testing with cURL

### 1. Login

```bash
curl -X POST http://localhost:8000/api/v1/webmail/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@mushqila.com",
    "password": "TestPass123"
  }'
```

**Response**:
```json
{
  "success": true,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {...},
    "account": {...}
  }
}
```

**Save the token** for subsequent requests.

### 2. Get Emails (Inbox)

```bash
curl -X GET "http://localhost:8000/api/v1/webmail/emails/?folder=inbox&page=1" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 3. Get Email Detail

```bash
curl -X GET "http://localhost:8000/api/v1/webmail/emails/{email_id}/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 4. Send Email

```bash
curl -X POST http://localhost:8000/api/v1/webmail/emails/send/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "to_addresses": ["recipient@example.com"],
    "subject": "Test Email from API",
    "body_text": "This is a test email sent via API",
    "body_html": "<p>This is a test email sent via API</p>"
  }'
```

### 5. Mark as Read

```bash
curl -X PATCH "http://localhost:8000/api/v1/webmail/emails/{email_id}/mark_read/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"is_read": true}'
```

### 6. Star Email

```bash
curl -X PATCH "http://localhost:8000/api/v1/webmail/emails/{email_id}/star/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"is_starred": true}'
```

### 7. Move to Folder

```bash
curl -X PATCH "http://localhost:8000/api/v1/webmail/emails/{email_id}/move/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"folder": "trash"}'
```

### 8. Search Emails

```bash
curl -X GET "http://localhost:8000/api/v1/webmail/emails/search/?q=meeting" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 9. Get Statistics

```bash
curl -X GET http://localhost:8000/api/v1/webmail/stats/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 10. Get Account Info

```bash
curl -X GET http://localhost:8000/api/v1/webmail/account/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 11. Change Password

```bash
curl -X POST http://localhost:8000/api/v1/webmail/auth/change-password/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "TestPass123",
    "new_password": "NewPass123",
    "confirm_password": "NewPass123"
  }'
```

### 12. Logout

```bash
curl -X POST http://localhost:8000/api/v1/webmail/auth/logout/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

---

## API Testing with Python

### Install requests library

```bash
pip install requests
```

### Test Script

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1/webmail"

# 1. Login
def login():
    response = requests.post(f"{BASE_URL}/auth/login/", json={
        "email": "test@mushqila.com",
        "password": "TestPass123"
    })
    data = response.json()
    if data['success']:
        return data['data']['token']
    return None

# 2. Get Emails
def get_emails(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/emails/?folder=inbox", headers=headers)
    return response.json()

# 3. Send Email
def send_email(token):
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "to_addresses": ["recipient@example.com"],
        "subject": "Test from Python",
        "body_text": "This is a test email",
        "body_html": "<p>This is a test email</p>"
    }
    response = requests.post(f"{BASE_URL}/emails/send/", headers=headers, json=data)
    return response.json()

# 4. Get Statistics
def get_stats(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/stats/", headers=headers)
    return response.json()

# Run tests
if __name__ == "__main__":
    print("1. Logging in...")
    token = login()
    if token:
        print(f"✓ Login successful! Token: {token[:20]}...")
        
        print("\n2. Getting emails...")
        emails = get_emails(token)
        print(f"✓ Found {emails['data']['count']} emails")
        
        print("\n3. Sending email...")
        result = send_email(token)
        if result['success']:
            print("✓ Email sent successfully!")
        
        print("\n4. Getting statistics...")
        stats = get_stats(token)
        print(f"✓ Total emails: {stats['data']['total_emails']}")
        print(f"✓ Unread: {stats['data']['unread_count']}")
    else:
        print("✗ Login failed!")
```

---

## API Testing with Postman

### 1. Import Collection

Create a new Postman collection with these requests:

#### Environment Variables
```
base_url: http://localhost:8000/api/v1/webmail
token: (will be set after login)
```

#### Requests

**1. Login**
- Method: POST
- URL: `{{base_url}}/auth/login/`
- Body (JSON):
```json
{
  "email": "test@mushqila.com",
  "password": "TestPass123"
}
```
- Tests (to save token):
```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.environment.set("token", jsonData.data.token);
}
```

**2. Get Emails**
- Method: GET
- URL: `{{base_url}}/emails/?folder=inbox`
- Headers: `Authorization: Bearer {{token}}`

**3. Send Email**
- Method: POST
- URL: `{{base_url}}/emails/send/`
- Headers: `Authorization: Bearer {{token}}`
- Body (JSON):
```json
{
  "to_addresses": ["recipient@example.com"],
  "subject": "Test Email",
  "body_text": "Test content",
  "body_html": "<p>Test content</p>"
}
```

---

## Flutter Integration Example

### 1. Add Dependencies (pubspec.yaml)

```yaml
dependencies:
  http: ^1.1.0
  shared_preferences: ^2.2.2
```

### 2. API Service Class

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class WebmailApiService {
  static const String baseUrl = 'https://mushqila.com/api/v1/webmail';
  
  // Login
  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
      }),
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      if (data['success']) {
        // Save token
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('token', data['data']['token']);
        await prefs.setString('refresh_token', data['data']['refresh_token']);
      }
      return data;
    }
    throw Exception('Login failed');
  }
  
  // Get Emails
  Future<Map<String, dynamic>> getEmails({String folder = 'inbox', int page = 1}) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    
    final response = await http.get(
      Uri.parse('$baseUrl/emails/?folder=$folder&page=$page'),
      headers: {
        'Authorization': 'Bearer $token',
      },
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load emails');
  }
  
  // Send Email
  Future<Map<String, dynamic>> sendEmail({
    required List<String> toAddresses,
    required String subject,
    required String bodyText,
    String? bodyHtml,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    
    final response = await http.post(
      Uri.parse('$baseUrl/emails/send/'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'to_addresses': toAddresses,
        'subject': subject,
        'body_text': bodyText,
        'body_html': bodyHtml ?? bodyText,
      }),
    );
    
    if (response.statusCode == 201) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to send email');
  }
  
  // Get Statistics
  Future<Map<String, dynamic>> getStats() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    
    final response = await http.get(
      Uri.parse('$baseUrl/stats/'),
      headers: {
        'Authorization': 'Bearer $token',
      },
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load stats');
  }
  
  // Logout
  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    final refreshToken = prefs.getString('refresh_token');
    
    await http.post(
      Uri.parse('$baseUrl/auth/logout/'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'refresh_token': refreshToken,
      }),
    );
    
    // Clear local storage
    await prefs.remove('token');
    await prefs.remove('refresh_token');
  }
}
```

### 3. Usage in Flutter

```dart
// Login
final apiService = WebmailApiService();
try {
  final result = await apiService.login('test@mushqila.com', 'TestPass123');
  if (result['success']) {
    print('Login successful!');
    // Navigate to home screen
  }
} catch (e) {
  print('Login error: $e');
}

// Get Emails
try {
  final emails = await apiService.getEmails(folder: 'inbox', page: 1);
  print('Total emails: ${emails['data']['count']}');
} catch (e) {
  print('Error: $e');
}

// Send Email
try {
  final result = await apiService.sendEmail(
    toAddresses: ['recipient@example.com'],
    subject: 'Hello from Flutter',
    bodyText: 'This is a test email from Flutter app',
  );
  if (result['success']) {
    print('Email sent!');
  }
} catch (e) {
  print('Error: $e');
}
```

---

## Common Issues & Solutions

### 1. CORS Error (Flutter Web)

Add CORS middleware to Django settings:

```bash
pip install django-cors-headers
```

```python
# settings.py
INSTALLED_APPS = [
    ...
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    ...
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://mushqila.com",
]
```

### 2. Token Expired

Implement token refresh:

```dart
Future<void> refreshToken() async {
  final prefs = await SharedPreferences.getInstance();
  final refreshToken = prefs.getString('refresh_token');
  
  final response = await http.post(
    Uri.parse('$baseUrl/auth/refresh/'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'refresh_token': refreshToken}),
  );
  
  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    await prefs.setString('token', data['data']['token']);
  }
}
```

### 3. 401 Unauthorized

- Check if token is valid
- Check if token is included in headers
- Try refreshing the token

---

## Production Checklist

- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable API logging
- [ ] Add API monitoring
- [ ] Set up error tracking (Sentry)
- [ ] Configure CDN for attachments
- [ ] Enable API caching
- [ ] Set up backup strategy
- [ ] Document all endpoints

---

## Support

For API issues:
1. Check Django logs
2. Check API response status codes
3. Verify authentication token
4. Review API documentation
5. Test with cURL/Postman first
