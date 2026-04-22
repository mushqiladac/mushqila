# 📱 Flutter API Quick Reference - Webmail

## 🔗 Base URL
```dart
static const baseUrl = 'https://mushqila.com/api/v1/webmail';
```

---

## 🔐 Authentication

### Login
```dart
POST /auth/login/
Body: {"email": "user@mushqila.com", "password": "pass123"}
Response: {"success": true, "data": {"token": "...", "refresh_token": "..."}}
```

### Logout
```dart
POST /auth/logout/
Headers: Authorization: Bearer {token}
Body: {"refresh_token": "..."}
```

### Refresh Token
```dart
POST /auth/refresh/
Body: {"refresh": "refresh_token"}
Response: {"access": "new_token", "refresh": "new_refresh"}
```

---

## 📧 Email Operations

### Get Emails
```dart
GET /emails/?folder=inbox&page=1
Headers: Authorization: Bearer {token}
Response: {"success": true, "data": {"count": 100, "results": [...]}}
```

### Email Detail
```dart
GET /emails/{id}/
Headers: Authorization: Bearer {token}
Response: {"success": true, "data": {...}}
```

### Send Email
```dart
POST /emails/send/
Headers: Authorization: Bearer {token}
Body: {
  "to_addresses": ["recipient@example.com"],
  "subject": "Subject",
  "body_text": "Text",
  "body_html": "<p>HTML</p>"
}
Response: {"success": true, "data": {"id": 123, "message_id": "..."}}
```

### Save Draft
```dart
POST /emails/draft/
Headers: Authorization: Bearer {token}
Body: {"to_addresses": [...], "subject": "...", "body_text": "..."}
Response: {"success": true, "data": {"id": 124}}
```

### Mark Read
```dart
PATCH /emails/{id}/mark_read/
Headers: Authorization: Bearer {token}
Body: {"is_read": true}
```

### Star Email
```dart
PATCH /emails/{id}/star/
Headers: Authorization: Bearer {token}
Body: {"is_starred": true}
```

### Move Email
```dart
PATCH /emails/{id}/move/
Headers: Authorization: Bearer {token}
Body: {"folder": "trash"}
```

### Delete Email
```dart
DELETE /emails/{id}/?permanent=false
Headers: Authorization: Bearer {token}
```

### Search
```dart
GET /emails/search/?q=meeting&folder=inbox
Headers: Authorization: Bearer {token}
Response: {"success": true, "data": {"count": 5, "results": [...]}}
```

---

## 👥 Contacts

### List Contacts
```dart
GET /contacts/
Headers: Authorization: Bearer {token}
Response: {"success": true, "data": {"count": 50, "results": [...]}}
```

### Create Contact
```dart
POST /contacts/
Headers: Authorization: Bearer {token}
Body: {"email": "contact@example.com", "name": "John Doe"}
Response: {"success": true, "data": {...}}
```

### Update Contact
```dart
PATCH /contacts/{id}/
Headers: Authorization: Bearer {token}
Body: {"name": "Updated Name", "is_favorite": true}
```

### Delete Contact
```dart
DELETE /contacts/{id}/
Headers: Authorization: Bearer {token}
```

---

## 👤 Account

### Get Account Info
```dart
GET /account/
Headers: Authorization: Bearer {token}
Response: {"success": true, "data": {...}}
```

### Update Account
```dart
PATCH /account/update/
Headers: Authorization: Bearer {token}
Body: {"display_name": "New Name", "signature": "..."}
```

---

## 📊 Statistics

### Get Stats
```dart
GET /stats/
Headers: Authorization: Bearer {token}
Response: {
  "success": true,
  "data": {
    "total_emails": 500,
    "unread_count": 45,
    "inbox_count": 150,
    "sent_count": 200,
    "drafts_count": 10,
    "trash_count": 30,
    "starred_count": 25,
    "storage_used_mb": 50.0
  }
}
```

---

## 📎 Attachments

### Download
```dart
GET /attachments/{id}/download/
Headers: Authorization: Bearer {token}
Response: {"success": true, "data": {"download_url": "...", "filename": "..."}}
```

---

## 🔑 Common Headers

```dart
final headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer $token',
};
```

---

## ⚠️ Error Handling

```dart
if (response.statusCode == 401) {
  // Token expired, refresh it
  await refreshToken();
  // Retry request
}

final data = jsonDecode(response.body);
if (!data['success']) {
  final error = data['error'];
  print('Error: ${error['code']} - ${error['message']}');
}
```

---

## 📦 Response Format

### Success
```json
{
  "success": true,
  "data": {...}
}
```

### Error
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message",
    "details": {...}
  }
}
```

---

## 🎯 Query Parameters

### Pagination
```dart
?page=1&page_size=20
```

### Filtering
```dart
?folder=inbox&is_read=false&is_starred=true
```

### Ordering
```dart
?ordering=-received_at  // Descending
?ordering=received_at   // Ascending
```

### Search
```dart
?q=meeting&folder=inbox&from=sender@example.com
```

---

## 🔐 Token Management

```dart
// Save token
final prefs = await SharedPreferences.getInstance();
await prefs.setString('token', token);
await prefs.setString('refresh_token', refreshToken);

// Get token
final token = prefs.getString('token');

// Clear token (logout)
await prefs.remove('token');
await prefs.remove('refresh_token');
```

---

## 📱 Complete Flutter Example

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class WebmailAPI {
  static const baseUrl = 'https://mushqila.com/api/v1/webmail';
  
  // Login
  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    
    final data = jsonDecode(response.body);
    if (data['success']) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('token', data['data']['token']);
      await prefs.setString('refresh_token', data['data']['refresh_token']);
    }
    return data;
  }
  
  // Get Token
  Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('token');
  }
  
  // Get Emails
  Future<Map<String, dynamic>> getEmails({
    String folder = 'inbox',
    int page = 1,
  }) async {
    final token = await _getToken();
    final response = await http.get(
      Uri.parse('$baseUrl/emails/?folder=$folder&page=$page'),
      headers: {'Authorization': 'Bearer $token'},
    );
    return jsonDecode(response.body);
  }
  
  // Send Email
  Future<Map<String, dynamic>> sendEmail({
    required List<String> toAddresses,
    required String subject,
    required String bodyText,
    String? bodyHtml,
  }) async {
    final token = await _getToken();
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
    return jsonDecode(response.body);
  }
  
  // Get Statistics
  Future<Map<String, dynamic>> getStats() async {
    final token = await _getToken();
    final response = await http.get(
      Uri.parse('$baseUrl/stats/'),
      headers: {'Authorization': 'Bearer $token'},
    );
    return jsonDecode(response.body);
  }
  
  // Refresh Token
  Future<bool> refreshToken() async {
    final prefs = await SharedPreferences.getInstance();
    final refreshToken = prefs.getString('refresh_token');
    
    final response = await http.post(
      Uri.parse('$baseUrl/auth/refresh/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'refresh': refreshToken}),
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      await prefs.setString('token', data['access']);
      return true;
    }
    return false;
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
      body: jsonEncode({'refresh_token': refreshToken}),
    );
    
    await prefs.remove('token');
    await prefs.remove('refresh_token');
  }
}

// Usage
void main() async {
  final api = WebmailAPI();
  
  // Login
  final loginResult = await api.login('user@mushqila.com', 'password');
  if (loginResult['success']) {
    print('Login successful!');
    
    // Get emails
    final emails = await api.getEmails(folder: 'inbox');
    print('Total emails: ${emails['data']['count']}');
    
    // Send email
    final sendResult = await api.sendEmail(
      toAddresses: ['recipient@example.com'],
      subject: 'Hello from Flutter',
      bodyText: 'This is a test email',
    );
    if (sendResult['success']) {
      print('Email sent!');
    }
    
    // Get stats
    final stats = await api.getStats();
    print('Unread: ${stats['data']['unread_count']}');
  }
}
```

---

## 🎨 UI Suggestions

### Email List Item
```dart
ListTile(
  leading: CircleAvatar(child: Text(email['from_name'][0])),
  title: Text(email['subject']),
  subtitle: Text(email['body_preview']),
  trailing: Column(
    children: [
      Text(formatDate(email['received_at'])),
      if (!email['is_read']) Icon(Icons.circle, size: 8, color: Colors.blue),
    ],
  ),
  onTap: () => openEmail(email['id']),
)
```

### Folder Navigation
```dart
folders = ['inbox', 'sent', 'drafts', 'trash', 'spam']
icons = [Icons.inbox, Icons.send, Icons.drafts, Icons.delete, Icons.report]
```

### Statistics Dashboard
```dart
GridView.count(
  crossAxisCount: 2,
  children: [
    StatCard('Total', stats['total_emails']),
    StatCard('Unread', stats['unread_count']),
    StatCard('Starred', stats['starred_count']),
    StatCard('Storage', '${stats['storage_used_mb']} MB'),
  ],
)
```

---

**Quick Reference Version:** 1.0  
**Last Updated:** 19 April 2026  
**Status:** ✅ Production Ready
