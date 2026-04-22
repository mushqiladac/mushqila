# B2B Travel Platform API - সম্পূর্ণ Endpoint তালিকা (Flutter App এর জন্য)

## 📱 API Base URL
```
Production: https://mushqila.com/api/v1/b2b
Local: http://localhost:8000/api/v1/b2b
```

---

## 🔐 Authentication Endpoints (৫টি)

### 1. Register (নিবন্ধন)
```
POST /auth/register/
```

**Request Body:**
```json
{
  "email": "agent@example.com",
  "password": "SecurePass123",
  "confirm_password": "SecurePass123",
  "first_name": "Ahmed",
  "last_name": "Ali",
  "phone": "+966512345678",
  "company_name_en": "Travel Agency",
  "company_name_ar": "وكالة السفر",
  "company_registration": "CR1234567890",
  "vat_number": "300123456789003",
  "user_type": "agent",
  "referral_code": "SA12345678"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Registration successful. Your account is pending approval.",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {...}
  }
}
```

---

### 2. Login (লগইন)
```
POST /auth/login/
```

**Request Body:**
```json
{
  "email": "agent@example.com",
  "password": "SecurePass123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
      "id": 1,
      "email": "agent@example.com",
      "first_name": "Ahmed",
      "last_name": "Ali",
      "phone": "+966512345678",
      "user_type": "agent",
      "status": "active",
      "company_name": "Travel Agency",
      "credit_limit": "50000.00",
      "current_balance": "-5000.00",
      "wallet_balance": "1000.00",
      "commission_rate": "5.00",
      "available_credit": "46000.00",
      "referral_code": "SA12345678",
      "kyc_verified": true
    }
  }
}
```

---

### 3. Logout (লগআউট)
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

---

### 4. Token Refresh (টোকেন রিফ্রেশ)
```
POST /auth/refresh/
```

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

### 5. Change Password (পাসওয়ার্ড পরিবর্তন)
```
POST /auth/change-password/
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "current_password": "OldPass123",
  "new_password": "NewPass456",
  "confirm_password": "NewPass456"
}
```

---

## 👤 Profile Endpoints (২টি)

### 6. Get Profile (প্রোফাইল দেখুন)
```
GET /profile/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "email": "agent@example.com",
    "first_name": "Ahmed",
    "last_name": "Ali",
    "phone": "+966512345678",
    "user_type": "agent",
    "status": "active",
    "company_name_en": "Travel Agency",
    "company_name_ar": "وكالة السفر",
    "company_registration": "CR1234567890",
    "vat_number": "300123456789003",
    "credit_limit": "50000.00",
    "current_balance": "-5000.00",
    "wallet_balance": "1000.00",
    "commission_rate": "5.00",
    "referral_code": "SA12345678",
    "scta_license": "SCTA123456",
    "hajj_license": "HAJJ789012",
    "iata_number": "12345678",
    "email_verified": true,
    "phone_verified": true,
    "kyc_verified": true,
    "city": 1,
    "city_name": "Riyadh",
    "region_name": "Riyadh Province",
    "address_en": "123 King Fahd Road",
    "address_ar": "١٢٣ طريق الملك فهد",
    "profile": {
      "business_type": "Travel Agency",
      "years_in_business": 5,
      "bank_name_en": "Al Rajhi Bank",
      "bank_name_ar": "مصرف الراجحي",
      "account_number": "1234567890",
      "iban": "SA0380000000608010167519",
      "total_bookings": 150,
      "total_sales": "500000.00",
      "total_commission": "25000.00",
      "hajj_bookings": 20,
      "umrah_bookings": 50,
      "language": "en",
      "timezone": "Asia/Riyadh"
    }
  }
}
```

---

### 7. Update Profile (প্রোফাইল আপডেট)
```
PATCH /profile/update/
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "first_name": "Ahmed Updated",
  "company_name_en": "New Travel Agency",
  "address_en": "456 New Street"
}
```

---

## 📊 Dashboard Endpoint (১টি)

### 8. Dashboard Statistics (ড্যাশবোর্ড পরিসংখ্যান)
```
GET /dashboard/stats/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_bookings": 150,
    "total_sales": "500000.00",
    "total_commission": "25000.00",
    "pending_bookings": 5,
    "confirmed_bookings": 120,
    "current_balance": "-5000.00",
    "wallet_balance": "1000.00",
    "available_credit": "46000.00",
    "unread_notifications": 3,
    "hajj_bookings": 20,
    "umrah_bookings": 50,
    "flight_bookings": 80,
    "hotel_bookings": 70
  }
}
```

---

## 💰 Transaction Endpoints (২টি)

### 9. Get Transactions (লেনদেন তালিকা)
```
GET /transactions/?page=1&type=booking&status=completed
Authorization: Bearer {token}
```

**Query Parameters:**
- `page`: Page number
- `page_size`: Items per page (default: 20)
- `type`: deposit, withdrawal, booking, hajj, umrah, refund, commission, adjustment
- `status`: pending, completed, failed, cancelled
- `from_date`: Start date (YYYY-MM-DD)
- `to_date`: End date (YYYY-MM-DD)

**Response:**
```json
{
  "success": true,
  "data": {
    "count": 100,
    "next": "...",
    "previous": null,
    "results": [
      {
        "id": 1,
        "transaction_id": "TRX1713532800ABC123",
        "user": 1,
        "user_email": "agent@example.com",
        "user_name": "Ahmed Ali",
        "transaction_type": "booking",
        "amount": "5000.00",
        "currency": "SAR",
        "status": "completed",
        "description": "Flight booking payment",
        "description_ar": "دفع حجز الطيران",
        "reference": "FLT1713532800XYZ789",
        "balance_before": "10000.00",
        "balance_after": "5000.00",
        "vat_amount": "750.00",
        "metadata": {},
        "created_at": "2026-04-19T10:30:00Z"
      }
    ]
  }
}
```

---

### 10. Get Transaction Detail (লেনদেন বিস্তারিত)
```
GET /transactions/{id}/
Authorization: Bearer {token}
```

---

## ✈️ Flight Booking Endpoints (৫টি)

### 11. Get Flight Bookings (ফ্লাইট বুকিং তালিকা)
```
GET /flight-bookings/?page=1&status=confirmed&travel_type=domestic
Authorization: Bearer {token}
```

**Query Parameters:**
- `page`: Page number
- `page_size`: Items per page
- `status`: pending, confirmed, ticketed, cancelled, refunded, void
- `travel_type`: domestic, international, hajj, umrah
- `search`: Search by booking ID, passenger name, or PNR
- `from_date`: Departure from date
- `to_date`: Departure to date

**Response:**
```json
{
  "success": true,
  "data": {
    "count": 80,
    "results": [
      {
        "id": 1,
        "booking_id": "FLT1713532800ABC123",
        "agent": 1,
        "agent_name": "Ahmed Ali",
        "passenger_name": "Mohammed Hassan",
        "airline_name": "Saudi Arabian Airlines",
        "flight_number": "SV123",
        "route": "Riyadh → Jeddah",
        "departure_date": "2026-05-01T10:00:00Z",
        "arrival_date": "2026-05-01T11:30:00Z",
        "travel_type": "domestic",
        "total_amount": "500.00",
        "commission_amount": "25.00",
        "status": "confirmed",
        "pnr": "ABC123",
        "created_at": "2026-04-19T10:30:00Z"
      }
    ]
  }
}
```

---

### 12. Get Flight Booking Detail (ফ্লাইট বুকিং বিস্তারিত)
```
GET /flight-bookings/{id}/
Authorization: Bearer {token}
```

---

### 13. Create Flight Booking (ফ্লাইট বুকিং তৈরি)
```
POST /flight-bookings/
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "passenger_name": "Mohammed Hassan",
  "passenger_name_ar": "محمد حسن",
  "passenger_email": "passenger@example.com",
  "passenger_phone": "+966512345678",
  "airline": 1,
  "flight_number": "SV123",
  "departure_city": "Riyadh",
  "arrival_city": "Jeddah",
  "departure_airport": "RUH",
  "arrival_airport": "JED",
  "departure_date": "2026-05-01T10:00:00Z",
  "arrival_date": "2026-05-01T11:30:00Z",
  "travel_type": "domestic",
  "booking_class": "Y",
  "base_fare": "400.00",
  "tax": "50.00",
  "vat": "50.00",
  "booking_notes": "Window seat preferred"
}
```

---

### 14. Update Flight Booking (ফ্লাইট বুকিং আপডেট)
```
PATCH /flight-bookings/{id}/
Authorization: Bearer {token}
```

---

### 15. Cancel Flight Booking (ফ্লাইট বুকিং বাতিল)
```
PATCH /flight-bookings/{id}/cancel/
Authorization: Bearer {token}
```

---

## 🏨 Hotel Booking Endpoints (৫টি)

### 16. Get Hotel Bookings (হোটেল বুকিং তালিকা)
```
GET /hotel-bookings/?page=1&status=confirmed
Authorization: Bearer {token}
```

### 17. Get Hotel Booking Detail
```
GET /hotel-bookings/{id}/
Authorization: Bearer {token}
```

### 18. Create Hotel Booking
```
POST /hotel-bookings/
Authorization: Bearer {token}
```

### 19. Update Hotel Booking
```
PATCH /hotel-bookings/{id}/
Authorization: Bearer {token}
```

### 20. Cancel Hotel Booking
```
PATCH /hotel-bookings/{id}/cancel/
Authorization: Bearer {token}
```

---

## 🕋 Hajj Package Endpoints (২টি)

### 21. Get Hajj Packages (হজ প্যাকেজ তালিকা)
```
GET /hajj-packages/?year=2026&min_price=10000&max_price=50000
Authorization: Bearer {token}
```

### 22. Get Hajj Package Detail
```
GET /hajj-packages/{id}/
Authorization: Bearer {token}
```

---

## 🕌 Umrah Package Endpoints (২টি)

### 23. Get Umrah Packages (উমরাহ প্যাকেজ তালিকা)
```
GET /umrah-packages/?package_type=standard&min_duration=7&max_duration=15
Authorization: Bearer {token}
```

### 24. Get Umrah Package Detail
```
GET /umrah-packages/{id}/
Authorization: Bearer {token}
```

---

## 🔔 Notification Endpoints (৫টি)

### 25. Get Notifications (বিজ্ঞপ্তি তালিকা)
```
GET /notifications/?is_read=false&type=booking
Authorization: Bearer {token}
```

### 26. Get Notification Detail
```
GET /notifications/{id}/
Authorization: Bearer {token}
```

### 27. Mark Notification as Read
```
PATCH /notifications/{id}/mark_read/
Authorization: Bearer {token}
```

### 28. Mark All Notifications as Read
```
POST /notifications/mark_all_read/
Authorization: Bearer {token}
```

### 29. Delete Notification
```
DELETE /notifications/{id}/
Authorization: Bearer {token}
```

---

## 📄 Document Endpoints (৪টি)

### 30. Get Documents (ডকুমেন্ট তালিকা)
```
GET /documents/?type=passport&status=verified
Authorization: Bearer {token}
```

### 31. Get Document Detail
```
GET /documents/{id}/
Authorization: Bearer {token}
```

### 32. Upload Document
```
POST /documents/
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

### 33. Delete Document
```
DELETE /documents/{id}/
Authorization: Bearer {token}
```

---

## 💳 Credit Request Endpoints (৩টি)

### 34. Get Credit Requests (ক্রেডিট অনুরোধ তালিকা)
```
GET /credit-requests/?status=pending
Authorization: Bearer {token}
```

### 35. Get Credit Request Detail
```
GET /credit-requests/{id}/
Authorization: Bearer {token}
```

### 36. Create Credit Request
```
POST /credit-requests/
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "requested_limit": "100000.00",
  "purpose": "Business expansion and increased booking volume"
}
```

---

## 📍 Location Endpoints (২টি)

### 37. Get Saudi Regions (সৌদি অঞ্চল)
```
GET /locations/regions/
Authorization: Bearer {token}
```

### 38. Get Saudi Cities (সৌদি শহর)
```
GET /locations/cities/?region=1&is_major=true
Authorization: Bearer {token}
```

---

## 🏢 Supplier Endpoint (১টি)

### 39. Get Service Suppliers (সেবা সরবরাহকারী)
```
GET /suppliers/?type=airline
Authorization: Bearer {token}
```

**Query Parameters:**
- `type`: airline, hotel, transport, insurance, visa, hajj, umrah, guide, other

---

## 📊 Total Endpoints: 39

- Authentication: 5
- Profile: 2
- Dashboard: 1
- Transactions: 2
- Flight Bookings: 5
- Hotel Bookings: 5
- Hajj Packages: 2
- Umrah Packages: 2
- Notifications: 5
- Documents: 4
- Credit Requests: 3
- Locations: 2
- Suppliers: 1

---

**সম্পূর্ণ B2B Travel Platform API Flutter app এর জন্য প্রস্তুত!**

**তৈরি করেছেন:** Mushqila Development Team  
**তারিখ:** ১৯ এপ্রিল, ২০২৬  
**সংস্করণ:** 1.0  
**স্ট্যাটাস:** Production Ready ✅
