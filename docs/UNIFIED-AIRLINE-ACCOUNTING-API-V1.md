# Unified Airline Accounting API v1

This document defines a single backend API contract for both:
- Web admin panel
- Flutter mobile app

Base URL: `/api/v1`
Auth: JWT Bearer token (`Authorization: Bearer <access_token>`)

---

## 1) Standard API Response Format

### Success
```json
{
  "success": true,
  "message": "Request successful",
  "data": {},
  "errors": null,
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 0
  }
}
```

### Error
```json
{
  "success": false,
  "message": "Validation failed",
  "data": null,
  "errors": {
    "amount": ["Amount must be greater than 0"]
  },
  "code": "VALIDATION_ERROR"
}
```

---

## 2) Roles and Access

- `super_user`: Full access (user CRUD, monitoring, reports, settings)
- `manager`: Sales, payment, report view and limited updates
- `agent_user`: Own sales, own outstanding, own reports
- `viewer`: Read-only reports

Notes:
- Super user can create/update/deactivate users.
- No hard delete for financial records; use status flags.

---

## 3) Authentication Endpoints

### POST `/auth/login/`
- Public
- Request:
```json
{
  "email": "admin@example.com",
  "password": "StrongPassword123"
}
```
- Response `data`:
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": {
    "id": 1,
    "name": "Admin User",
    "email": "admin@example.com",
    "role": "super_user"
  }
}
```

### POST `/auth/refresh/`
- Public with refresh token

### POST `/auth/logout/`
- Auth required
- Blacklist refresh token

### GET `/auth/me/`
- Auth required
- Returns current user profile + role + permissions

---

## 4) User Management (Super User)

### GET `/users/`
- Filters: `role`, `status`, `search`, `page`, `limit`

### POST `/users/`
- Create user
- Request:
```json
{
  "full_name": "Agent One",
  "email": "agent1@example.com",
  "phone": "+8801XXXXXXXXX",
  "role": "agent_user",
  "password": "TempPass123!",
  "credit_limit": "100000.00",
  "is_active": true
}
```

### GET `/users/{id}/`

### PATCH `/users/{id}/`

### PATCH `/users/{id}/status/`
- Activate / suspend / block

### POST `/users/{id}/reset-password/`

---

## 5) Airlines

### GET `/airlines/`

### POST `/airlines/`
```json
{
  "code": "EK",
  "name": "Emirates",
  "country": "UAE",
  "settlement_days": 15,
  "is_active": true
}
```

### GET `/airlines/{id}/`

### PATCH `/airlines/{id}/`

---

## 6) Sales / Ticket Operations

### GET `/sales/`
Filters:
- `from_date`, `to_date`
- `airline_id`
- `user_id`
- `status` (`issued`, `void`, `refund`, `reissue`)
- `search` (pnr/ticket/passenger)

### POST `/sales/`
```json
{
  "airline_id": 2,
  "user_id": 10,
  "pnr": "ABC123",
  "ticket_number": "1761234567890",
  "issue_date": "2026-04-29",
  "travel_date": "2026-05-02",
  "route": "DAC-DXB-DAC",
  "passenger_name": "John Doe",
  "base_fare": "500.00",
  "tax_amount": "80.00",
  "other_fee": "20.00",
  "commission_amount": "15.00",
  "customer_price": "615.00",
  "airline_cost": "600.00",
  "status": "issued",
  "remarks": "N/A"
}
```

### GET `/sales/{id}/`

### PATCH `/sales/{id}/`

### POST `/sales/{id}/void/`

### POST `/sales/{id}/refund/`

### POST `/sales/{id}/reissue/`

Business rules:
- Any status change must create audit log.
- Any financial change must create transaction log + ledger entry.

---

## 7) Payment / Collection

### GET `/payments/`
Filters: `from_date`, `to_date`, `user_id`, `payment_method`, `airline_id`

### POST `/payments/`
```json
{
  "user_id": 10,
  "airline_id": 2,
  "received_date": "2026-04-29",
  "amount": "1000.00",
  "payment_method": "bank_transfer",
  "reference_no": "TXN-889922",
  "notes": "Partial collection"
}
```

### GET `/payments/{id}/`

### POST `/payments/{id}/allocate/`
- Allocate one payment across multiple sales

---

## 8) Outstanding / Due

### GET `/outstanding/summary/`
Returns:
- total receivable
- total payable
- overdue amount
- on-time amount

### GET `/outstanding/users/{user_id}/`
- User-wise outstanding details

### GET `/outstanding/airline-wise/`
- Airline-wise due/payable

### GET `/outstanding/aging/`
Buckets:
- `0_7_days`
- `8_15_days`
- `16_30_days`
- `31_plus_days`

---

## 9) Dashboard / Monitoring

### GET `/dashboard/super/`
Cards:
- total sales
- total collection
- outstanding
- overdue
- top 10 debt users

### GET `/dashboard/user/`
- own sales
- own collection
- own outstanding
- own monthly trend

### GET `/dashboard/kpi/`
- comparative KPI by date range

---

## 10) Reports

All report endpoints support:
- `from_date`, `to_date`
- `user_id` (super only)
- `airline_id`
- `format` (`json`, `csv`, `xlsx`, `pdf`)

### GET `/reports/sales/`

### GET `/reports/outstanding/`

### GET `/reports/collection/`

### GET `/reports/commission/`

### GET `/reports/profitability/`

### GET `/reports/user-performance/`

---

## 11) Audit and Security

### GET `/audit/activities/`
- login, user actions, critical operations

### GET `/audit/transactions/`
- financial state changes

Security rules:
- Log IP and user agent for critical updates
- No delete endpoint for sales/payments after posting
- Use `PATCH .../status/` for deactivation

---

## 12) Flutter Integration Rules

- Use one API client with token interceptor
- Refresh token on 401 once; then force logout
- Paginated list response required for all list endpoints
- Date format: ISO-8601 (`YYYY-MM-DD` or datetime UTC)
- Decimal values as string in JSON to avoid precision loss

Recommended app modules:
- `auth`
- `dashboard`
- `users` (super only)
- `airlines`
- `sales`
- `payments`
- `outstanding`
- `reports`
- `settings`

---

## 13) Suggested Implementation Order

1. Auth + role permission matrix
2. User and airline master data
3. Sales create/list/detail/update
4. Payment + allocation
5. Outstanding calculator + aging
6. Dashboard endpoints
7. Report endpoints + export
8. Audit log hardening and rate limits

---

## 14) Backward Compatibility

- Keep existing APIs untouched:
  - `/api/v1/b2b/...`
  - `/api/v1/webmail/...`
- Add new namespace:
  - `/api/v1/accounting/...`

This allows phased rollout for web and Flutter without breaking current clients.
