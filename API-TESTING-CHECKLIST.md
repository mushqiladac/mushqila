# Webmail API Testing Checklist

## ✅ Pre-Testing Setup

- [ ] Database configured (DB_HOST=localhost for local)
- [ ] Dependencies installed: `pip install djangorestframework-simplejwt==5.3.0`
- [ ] Migrations run: `python manage.py migrate`
- [ ] Test account created: `python manage.py create_webmail_account --email test@mushqila.com --password TestPass123 --first-name Test --last-name User --alternate-email test@gmail.com`
- [ ] Server running: `python manage.py runserver`

---

## 🔐 Authentication Endpoints (6/6)

### 1. Login
- [ ] POST `/api/v1/webmail/auth/login/`
- [ ] Valid credentials return token
- [ ] Invalid credentials return 401
- [ ] Missing fields return validation error
- [ ] Token format is valid JWT

**Test Command:**
```bash
curl -X POST http://localhost:8000/api/v1/webmail/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@mushqila.com", "password": "TestPass123"}'
```

### 2. Logout
- [ ] POST `/api/v1/webmail/auth/logout/`
- [ ] Token blacklisted successfully
- [ ] Requires authentication
- [ ] Invalid token returns error

**Test Command:**
```bash
curl -X POST http://localhost:8000/api/v1/webmail/auth/logout/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

### 3. Token Refresh
- [ ] POST `/api/v1/webmail/auth/refresh/`
- [ ] Valid refresh token returns new access token
- [ ] Invalid refresh token returns error
- [ ] Expired refresh token returns error

**Test Command:**
```bash
curl -X POST http://localhost:8000/api/v1/webmail/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

### 4. Forgot Password
- [ ] POST `/api/v1/webmail/auth/forgot-password/`
- [ ] Valid email sends temporary password
- [ ] Invalid email returns success (security)
- [ ] No alternate email returns error

**Test Command:**
```bash
curl -X POST http://localhost:8000/api/v1/webmail/auth/forgot-password/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@mushqila.com"}'
```

### 5. Reset Password
- [ ] POST `/api/v1/webmail/auth/reset-password/`
- [ ] Valid temp password resets password
- [ ] Invalid temp password returns error
- [ ] Expired temp password returns error
- [ ] Password mismatch returns error

**Test Command:**
```bash
curl -X POST http://localhost:8000/api/v1/webmail/auth/reset-password/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@mushqila.com", "temporary_password": "TEMP123", "new_password": "NewPass123", "confirm_password": "NewPass123"}'
```

### 6. Change Password
- [ ] POST `/api/v1/webmail/auth/change-password/`
- [ ] Valid current password changes password
- [ ] Invalid current password returns error
- [ ] Password mismatch returns error
- [ ] Requires authentication

**Test Command:**
```bash
curl -X POST http://localhost:8000/api/v1/webmail/auth/change-password/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_password": "TestPass123", "new_password": "NewPass456", "confirm_password": "NewPass456"}'
```

---

## 📧 Email Endpoints (9/9)

### 7. List Emails
- [ ] GET `/api/v1/webmail/emails/`
- [ ] Returns paginated results
- [ ] Filter by folder works
- [ ] Filter by is_read works
- [ ] Filter by is_starred works
- [ ] Ordering works
- [ ] Pagination works (page, page_size)
- [ ] Requires authentication

**Test Command:**
```bash
curl -X GET "http://localhost:8000/api/v1/webmail/emails/?folder=inbox&page=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 8. Email Detail
- [ ] GET `/api/v1/webmail/emails/{id}/`
- [ ] Returns full email data
- [ ] Includes attachments
- [ ] Marks email as read
- [ ] Requires authentication
- [ ] Returns 404 for non-existent email

**Test Command:**
```bash
curl -X GET "http://localhost:8000/api/v1/webmail/emails/1/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 9. Send Email
- [ ] POST `/api/v1/webmail/emails/send/`
- [ ] Sends email successfully
- [ ] Returns email ID and message ID
- [ ] Validates required fields
- [ ] Handles CC/BCC
- [ ] Supports HTML and text
- [ ] Requires authentication

**Test Command:**
```bash
curl -X POST http://localhost:8000/api/v1/webmail/emails/send/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to_addresses": ["recipient@example.com"], "subject": "Test", "body_text": "Test email", "body_html": "<p>Test email</p>"}'
```

### 10. Save Draft
- [ ] POST `/api/v1/webmail/emails/draft/`
- [ ] Saves draft successfully
- [ ] Returns draft ID
- [ ] Optional fields work
- [ ] Requires authentication

**Test Command:**
```bash
curl -X POST http://localhost:8000/api/v1/webmail/emails/draft/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to_addresses": ["recipient@example.com"], "subject": "Draft", "body_text": "Draft content"}'
```

### 11. Mark Read/Unread
- [ ] PATCH `/api/v1/webmail/emails/{id}/mark_read/`
- [ ] Marks as read
- [ ] Marks as unread
- [ ] Updates read_at timestamp
- [ ] Requires authentication

**Test Command:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/webmail/emails/1/mark_read/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_read": true}'
```

### 12. Star/Unstar
- [ ] PATCH `/api/v1/webmail/emails/{id}/star/`
- [ ] Stars email
- [ ] Unstars email
- [ ] Requires authentication

**Test Command:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/webmail/emails/1/star/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_starred": true}'
```

### 13. Move to Folder
- [ ] PATCH `/api/v1/webmail/emails/{id}/move/`
- [ ] Moves to valid folder
- [ ] Rejects invalid folder
- [ ] Requires authentication

**Test Command:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/webmail/emails/1/move/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"folder": "trash"}'
```

### 14. Delete Email
- [ ] DELETE `/api/v1/webmail/emails/{id}/`
- [ ] Soft delete (move to trash)
- [ ] Permanent delete with parameter
- [ ] Requires authentication

**Test Command:**
```bash
# Soft delete
curl -X DELETE "http://localhost:8000/api/v1/webmail/emails/1/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Permanent delete
curl -X DELETE "http://localhost:8000/api/v1/webmail/emails/1/?permanent=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 15. Search Emails
- [ ] GET `/api/v1/webmail/emails/search/`
- [ ] Searches in subject
- [ ] Searches in from_address
- [ ] Searches in body_text
- [ ] Filter by folder works
- [ ] Filter by from works
- [ ] Pagination works
- [ ] Requires authentication

**Test Command:**
```bash
curl -X GET "http://localhost:8000/api/v1/webmail/emails/search/?q=meeting" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 👥 Contact Endpoints (5/5)

### 16. List Contacts
- [ ] GET `/api/v1/webmail/contacts/`
- [ ] Returns paginated results
- [ ] Ordered by favorite then name
- [ ] Requires authentication

**Test Command:**
```bash
curl -X GET "http://localhost:8000/api/v1/webmail/contacts/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 17. Contact Detail
- [ ] GET `/api/v1/webmail/contacts/{id}/`
- [ ] Returns full contact data
- [ ] Requires authentication
- [ ] Returns 404 for non-existent contact

**Test Command:**
```bash
curl -X GET "http://localhost:8000/api/v1/webmail/contacts/1/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 18. Create Contact
- [ ] POST `/api/v1/webmail/contacts/`
- [ ] Creates contact successfully
- [ ] Validates email format
- [ ] Requires authentication

**Test Command:**
```bash
curl -X POST http://localhost:8000/api/v1/webmail/contacts/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "contact@example.com", "name": "John Doe", "company": "ABC Corp"}'
```

### 19. Update Contact
- [ ] PATCH `/api/v1/webmail/contacts/{id}/`
- [ ] Updates contact successfully
- [ ] Partial update works
- [ ] Requires authentication

**Test Command:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/webmail/contacts/1/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe Updated", "is_favorite": true}'
```

### 20. Delete Contact
- [ ] DELETE `/api/v1/webmail/contacts/{id}/`
- [ ] Deletes contact successfully
- [ ] Requires authentication

**Test Command:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/webmail/contacts/1/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 👤 Account Endpoints (2/2)

### 21. Get Account Info
- [ ] GET `/api/v1/webmail/account/`
- [ ] Returns account data
- [ ] Requires authentication

**Test Command:**
```bash
curl -X GET http://localhost:8000/api/v1/webmail/account/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 22. Update Account
- [ ] PATCH `/api/v1/webmail/account/update/`
- [ ] Updates account successfully
- [ ] Partial update works
- [ ] Requires authentication

**Test Command:**
```bash
curl -X PATCH http://localhost:8000/api/v1/webmail/account/update/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"display_name": "Updated Name", "signature": "New signature"}'
```

---

## 📊 Statistics Endpoint (1/1)

### 23. Get Statistics
- [ ] GET `/api/v1/webmail/stats/`
- [ ] Returns all statistics
- [ ] Calculates storage correctly
- [ ] Requires authentication

**Test Command:**
```bash
curl -X GET http://localhost:8000/api/v1/webmail/stats/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📎 Attachment Endpoint (1/1)

### 24. Download Attachment
- [ ] GET `/api/v1/webmail/attachments/{id}/download/`
- [ ] Returns download URL
- [ ] Checks ownership
- [ ] Requires authentication

**Test Command:**
```bash
curl -X GET "http://localhost:8000/api/v1/webmail/attachments/UUID/download/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔒 Security Tests

- [ ] Unauthenticated requests return 401
- [ ] Invalid token returns 401
- [ ] Expired token returns 401
- [ ] User can only access own data
- [ ] CSRF protection works
- [ ] SQL injection prevented
- [ ] XSS prevention works

---

## 📱 Response Format Tests

- [ ] All success responses have `success: true`
- [ ] All error responses have `success: false`
- [ ] Error responses include error code
- [ ] Error responses include error message
- [ ] Pagination format is consistent
- [ ] Date format is ISO 8601

---

## ⚡ Performance Tests

- [ ] List endpoints respond < 500ms
- [ ] Detail endpoints respond < 200ms
- [ ] Search responds < 1s
- [ ] Pagination works with 100 items
- [ ] No N+1 query problems

---

## 🌐 CORS Tests (for Flutter Web)

- [ ] CORS headers present
- [ ] Preflight requests work
- [ ] Credentials allowed

---

## 📝 Summary

**Total Endpoints:** 24
- ✅ Tested: __/24
- ❌ Failed: __/24
- ⏭️ Skipped: __/24

**Test Date:** ___________
**Tester:** ___________
**Environment:** Local / Staging / Production

---

## 🐛 Issues Found

| # | Endpoint | Issue | Severity | Status |
|---|----------|-------|----------|--------|
| 1 |          |       |          |        |
| 2 |          |       |          |        |
| 3 |          |       |          |        |

---

## ✅ Sign-off

- [ ] All critical endpoints tested
- [ ] All security tests passed
- [ ] Documentation updated
- [ ] Ready for Flutter integration

**Approved by:** ___________
**Date:** ___________
