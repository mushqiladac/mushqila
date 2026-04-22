# 📱 B2B Travel Platform - Flutter API Quick Reference

## 🔗 Base URL
```dart
static const baseUrl = 'https://mushqila.com/api/v1/b2b';
```

---

## 🔐 Authentication

### Register
```dart
POST /auth/register/
Body: {
  "email": "agent@example.com",
  "password": "pass123",
  "confirm_password": "pass123",
  "first_name": "Ahmed",
  "last_name": "Ali",
  "phone": "+966512345678",
  "company_name_en": "Travel Agency",
  "user_type": "agent"
}
```

### Login
```dart
POST /auth/login/
Body: {"email": "agent@example.com", "password": "pass123"}
Response: {"success": true, "data": {"token": "...", "user": {...}}}
```

### Logout
```dart
POST /auth/logout/
Headers: Authorization: Bearer {token}
Body: {"refresh_token": "..."}
```

---

## 📊 Dashboard

### Get Statistics
```dart
GET /dashboard/stats/
Headers: Authorization: Bearer {token}
Response: {
  "success": true,
  "data": {
    "total_bookings": 150,
    "total_sales": "500000.00",
    "total_commission": "25000.00",
    "current_balance": "-5000.00",
    "available_credit": "46000.00",
    "unread_notifications": 3
  }
}
```

---

## ✈️ Flight Bookings

### List Flights
```dart
GET /flight-bookings/?page=1&status=confirmed
Headers: Authorization: Bearer {token}
```

### Create Flight Booking
```dart
POST /flight-bookings/
Headers: Authorization: Bearer {token}
Body: {
  "passenger_name": "Mohammed Hassan",
  "airline": 1,
  "flight_number": "SV123",
  "departure_city": "Riyadh",
  "arrival_city": "Jeddah",
  "departure_date": "2026-05-01T10:00:00Z",
  "arrival_date": "2026-05-01T11:30:00Z",
  "travel_type": "domestic",
  "base_fare": "400.00"
}
```

### Cancel Booking
```dart
PATCH /flight-bookings/{id}/cancel/
Headers: Authorization: Bearer {token}
```

---

## 🏨 Hotel Bookings

### List Hotels
```dart
GET /hotel-bookings/?page=1
Headers: Authorization: Bearer {token}
```

### Create Hotel Booking
```dart
POST /hotel-bookings/
Headers: Authorization: Bearer {token}
Body: {
  "hotel": 1,
  "guest_name": "Ahmed Ali",
  "check_in": "2026-05-01",
  "check_out": "2026-05-05",
  "rooms": 2,
  "adults": 2,
  "room_rate": "300.00"
}
```

---

## 🕋 Hajj & Umrah

### Get Hajj Packages
```dart
GET /hajj-packages/?year=2026
Headers: Authorization: Bearer {token}
```

### Get Umrah Packages
```dart
GET /umrah-packages/?package_type=standard
Headers: Authorization: Bearer {token}
```

---

## 💰 Transactions

### Get Transactions
```dart
GET /transactions/?type=booking&status=completed
Headers: Authorization: Bearer {token}
```

---

## 🔔 Notifications

### Get Notifications
```dart
GET /notifications/?is_read=false
Headers: Authorization: Bearer {token}
```

### Mark as Read
```dart
PATCH /notifications/{id}/mark_read/
Headers: Authorization: Bearer {token}
```

### Mark All as Read
```dart
POST /notifications/mark_all_read/
Headers: Authorization: Bearer {token}
```

---

## 📄 Documents

### Upload Document
```dart
POST /documents/
Headers: Authorization: Bearer {token}
Content-Type: multipart/form-data
Body: {
  "document_type": "passport",
  "document_number": "A12345678",
  "document_file": File
}
```

---

## 💳 Credit Requests

### Create Credit Request
```dart
POST /credit-requests/
Headers: Authorization: Bearer {token}
Body: {
  "requested_limit": "100000.00",
  "purpose": "Business expansion"
}
```

---

## 📍 Locations

### Get Regions
```dart
GET /locations/regions/
Headers: Authorization: Bearer {token}
```

### Get Cities
```dart
GET /locations/cities/?region=1
Headers: Authorization: Bearer {token}
```

---

## 🏢 Suppliers

### Get Suppliers
```dart
GET /suppliers/?type=airline
Headers: Authorization: Bearer {token}
```

---

## 📱 Complete Flutter Example

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class B2BAPI {
  static const baseUrl = 'https://mushqila.com/api/v1/b2b';
  
  // Register
  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    required String phone,
    required String companyName,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/register/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
        'confirm_password': password,
        'first_name': firstName,
        'last_name': lastName,
        'phone': phone,
        'company_name_en': companyName,
        'user_type': 'agent',
      }),
    );
    return jsonDecode(response.body);
  }
  
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
  
  // Get Dashboard Stats
  Future<Map<String, dynamic>> getDashboardStats() async {
    final token = await _getToken();
    final response = await http.get(
      Uri.parse('$baseUrl/dashboard/stats/'),
      headers: {'Authorization': 'Bearer $token'},
    );
    return jsonDecode(response.body);
  }
  
  // Get Flight Bookings
  Future<Map<String, dynamic>> getFlightBookings({
    int page = 1,
    String? status,
    String? travelType,
  }) async {
    final token = await _getToken();
    var url = '$baseUrl/flight-bookings/?page=$page';
    if (status != null) url += '&status=$status';
    if (travelType != null) url += '&travel_type=$travelType';
    
    final response = await http.get(
      Uri.parse(url),
      headers: {'Authorization': 'Bearer $token'},
    );
    return jsonDecode(response.body);
  }
  
  // Create Flight Booking
  Future<Map<String, dynamic>> createFlightBooking({
    required String passengerName,
    required int airlineId,
    required String flightNumber,
    required String departureCity,
    required String arrivalCity,
    required String departureDate,
    required String arrivalDate,
    required String travelType,
    required String baseFare,
  }) async {
    final token = await _getToken();
    final response = await http.post(
      Uri.parse('$baseUrl/flight-bookings/'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'passenger_name': passengerName,
        'airline': airlineId,
        'flight_number': flightNumber,
        'departure_city': departureCity,
        'arrival_city': arrivalCity,
        'departure_airport': 'RUH',
        'arrival_airport': 'JED',
        'departure_date': departureDate,
        'arrival_date': arrivalDate,
        'travel_type': travelType,
        'booking_class': 'Y',
        'base_fare': baseFare,
        'tax': '50.00',
        'vat': '50.00',
      }),
    );
    return jsonDecode(response.body);
  }
  
  // Get Notifications
  Future<Map<String, dynamic>> getNotifications({bool? isRead}) async {
    final token = await _getToken();
    var url = '$baseUrl/notifications/';
    if (isRead != null) url += '?is_read=$isRead';
    
    final response = await http.get(
      Uri.parse(url),
      headers: {'Authorization': 'Bearer $token'},
    );
    return jsonDecode(response.body);
  }
  
  // Mark Notification as Read
  Future<Map<String, dynamic>> markNotificationRead(int id) async {
    final token = await _getToken();
    final response = await http.patch(
      Uri.parse('$baseUrl/notifications/$id/mark_read/'),
      headers: {'Authorization': 'Bearer $token'},
    );
    return jsonDecode(response.body);
  }
  
  // Get Transactions
  Future<Map<String, dynamic>> getTransactions({
    int page = 1,
    String? type,
    String? status,
  }) async {
    final token = await _getToken();
    var url = '$baseUrl/transactions/?page=$page';
    if (type != null) url += '&type=$type';
    if (status != null) url += '&status=$status';
    
    final response = await http.get(
      Uri.parse(url),
      headers: {'Authorization': 'Bearer $token'},
    );
    return jsonDecode(response.body);
  }
  
  // Get Hajj Packages
  Future<Map<String, dynamic>> getHajjPackages({int? year}) async {
    final token = await _getToken();
    var url = '$baseUrl/hajj-packages/';
    if (year != null) url += '?year=$year';
    
    final response = await http.get(
      Uri.parse(url),
      headers: {'Authorization': 'Bearer $token'},
    );
    return jsonDecode(response.body);
  }
  
  // Get Umrah Packages
  Future<Map<String, dynamic>> getUmrahPackages({String? packageType}) async {
    final token = await _getToken();
    var url = '$baseUrl/umrah-packages/';
    if (packageType != null) url += '?package_type=$packageType';
    
    final response = await http.get(
      Uri.parse(url),
      headers: {'Authorization': 'Bearer $token'},
    );
    return jsonDecode(response.body);
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

// Usage Example
void main() async {
  final api = B2BAPI();
  
  // Login
  final loginResult = await api.login('agent@example.com', 'password');
  if (loginResult['success']) {
    print('Login successful!');
    
    // Get dashboard stats
    final stats = await api.getDashboardStats();
    print('Total Bookings: ${stats['data']['total_bookings']}');
    print('Available Credit: ${stats['data']['available_credit']}');
    
    // Get flight bookings
    final flights = await api.getFlightBookings(status: 'confirmed');
    print('Flight Bookings: ${flights['data']['count']}');
    
    // Get notifications
    final notifications = await api.getNotifications(isRead: false);
    print('Unread Notifications: ${notifications['data']['count']}');
  }
}
```

---

## 🎨 UI Suggestions

### Dashboard Cards
```dart
GridView.count(
  crossAxisCount: 2,
  children: [
    StatCard('Total Bookings', stats['total_bookings']),
    StatCard('Total Sales', '${stats['total_sales']} SAR'),
    StatCard('Commission', '${stats['total_commission']} SAR'),
    StatCard('Available Credit', '${stats['available_credit']} SAR'),
  ],
)
```

### Booking List Item
```dart
ListTile(
  leading: Icon(Icons.flight),
  title: Text(booking['passenger_name']),
  subtitle: Text('${booking['route']} - ${booking['flight_number']}'),
  trailing: Chip(
    label: Text(booking['status']),
    backgroundColor: getStatusColor(booking['status']),
  ),
  onTap: () => openBookingDetail(booking['id']),
)
```

---

**Quick Reference Version:** 1.0  
**Last Updated:** 19 April 2026  
**Status:** ✅ Production Ready
