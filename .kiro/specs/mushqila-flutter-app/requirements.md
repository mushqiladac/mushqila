# Requirements Document

## Introduction

The Mushqila Flutter App is a B2C mobile application for iOS and Android that allows general travelers to search and book flights, manage bookings, track PNRs, earn loyalty points, and receive push notifications. The app consumes REST APIs from the existing Mushqila Django backend (mushqila.com), which integrates with the Travelport Galileo GDS for live flight data. The app supports Arabic and English to serve the Saudi Arabia travel market.

---

## Glossary

- **App**: The Mushqila Flutter mobile application for iOS and Android.
- **API**: The Django REST Framework backend at mushqila.com that the App consumes.
- **Customer**: A registered B2C traveler using the App.
- **GDS**: Global Distribution System — Travelport Galileo, used for live flight inventory.
- **PNR**: Passenger Name Record — a unique booking reference code issued by the GDS.
- **Booking**: A confirmed flight reservation associated with a PNR and one or more Passengers.
- **Passenger**: A traveler included in a Booking, with personal and document details.
- **E-ticket**: A PDF document representing a confirmed, ticketed flight Booking.
- **Loyalty_Points**: Reward points earned by a Customer per booking, redeemable against future bookings.
- **Loyalty_Tier**: A Customer's reward tier (Bronze, Silver, Gold, Platinum) based on accumulated Loyalty_Points.
- **Push_Notification**: A device-level alert sent to the App via FCM (Firebase Cloud Messaging).
- **Auth_Token**: A JWT or DRF token issued by the API upon successful authentication.
- **OTP**: One-Time Password sent via SMS or email for identity verification.
- **Payment_Gateway**: The third-party payment processor integrated with the API (e.g., Stripe, SSLCommerz, or Tap Payments for Saudi market).
- **Locale**: The active language setting of the App — either `en` (English) or `ar` (Arabic).

---

## Requirements

### Requirement 1: User Registration

**User Story:** As a new traveler, I want to register an account, so that I can access booking and loyalty features.

#### Acceptance Criteria

1. THE App SHALL provide a registration form collecting full name, email address, phone number, password, and preferred language (Arabic or English).
2. WHEN a Customer submits the registration form, THE API SHALL create a Customer record and return an Auth_Token.
3. WHEN a Customer submits a registration form with an already-registered email address, THE API SHALL return a 400 error with a descriptive message.
4. WHEN a Customer submits a registration form with a password shorter than 8 characters, THE App SHALL display a validation error before submitting to the API.
5. AFTER successful registration, THE App SHALL send an OTP to the Customer's phone number or email for account verification.
6. WHEN a Customer submits a valid OTP, THE API SHALL mark the Customer's account as verified.
7. IF the OTP expires before submission, THEN THE API SHALL return an error and THE App SHALL offer to resend the OTP.

---

### Requirement 2: User Authentication

**User Story:** As a registered Customer, I want to log in and log out securely, so that my account and bookings are protected.

#### Acceptance Criteria

1. THE App SHALL provide a login screen accepting email address and password.
2. WHEN a Customer submits valid credentials, THE API SHALL return an Auth_Token and Customer profile data.
3. WHEN a Customer submits invalid credentials, THE API SHALL return a 401 error and THE App SHALL display a descriptive error message.
4. THE App SHALL store the Auth_Token securely using platform-level secure storage (iOS Keychain / Android Keystore).
5. WHEN an Auth_Token expires, THE App SHALL automatically attempt a token refresh before prompting the Customer to log in again.
6. WHEN a Customer taps "Forgot Password", THE App SHALL initiate a password reset flow via OTP sent to the registered email or phone number.
7. WHEN a Customer logs out, THE App SHALL delete the stored Auth_Token and navigate to the login screen.
8. WHERE biometric authentication is available on the device, THE App SHALL offer fingerprint or Face ID login as an alternative to password entry.

---

### Requirement 3: Flight Search

**User Story:** As a Customer, I want to search for available flights, so that I can find the best options for my trip.

#### Acceptance Criteria

1. THE App SHALL provide a flight search screen supporting one-way, round-trip, and multi-city search modes.
2. WHEN a Customer submits a one-way search with origin, destination, departure date, cabin class, and passenger counts, THE API SHALL return a list of available flight itineraries from the GDS.
3. WHEN a Customer submits a round-trip search, THE API SHALL return paired outbound and return itineraries.
4. WHEN a Customer submits a multi-city search with up to 4 legs, THE API SHALL return available itineraries for each leg.
5. THE App SHALL allow the Customer to filter search results by price range, airline, number of stops, and departure time window.
6. THE App SHALL allow the Customer to sort search results by price (ascending/descending), duration, and departure time.
7. WHEN no flights are available for the given search criteria, THE App SHALL display a "no results" message and suggest alternative dates.
8. IF the GDS returns an error during search, THEN THE API SHALL return a 503 error and THE App SHALL display a user-friendly error message without exposing technical details.
9. WHILE a flight search is in progress, THE App SHALL display a loading indicator.
10. THE App SHALL display each itinerary result with airline name, flight number, departure and arrival times, duration, number of stops, cabin class, and total price in the Customer's preferred currency.

---

### Requirement 4: Flight Booking

**User Story:** As a Customer, I want to book a selected flight, so that I can confirm my travel plans.

#### Acceptance Criteria

1. WHEN a Customer selects a flight itinerary, THE App SHALL display a booking form requesting Passenger details (title, first name, last name, date of birth, gender, nationality, passport number, passport expiry).
2. THE App SHALL allow the Customer to pre-fill Passenger details from saved TravelCompanion records stored in the Customer's profile.
3. WHEN a Customer submits a booking with complete Passenger details, THE API SHALL create a Booking record, call the GDS to generate a PNR, and return the PNR and Booking ID.
4. WHEN the GDS fails to generate a PNR, THEN THE API SHALL return a 502 error and THE App SHALL display a retry option.
5. THE App SHALL display a booking summary screen showing itinerary details, Passenger names, total price, and applicable taxes before final confirmation.
6. WHEN a Customer confirms the booking, THE App SHALL proceed to the payment screen.
7. WHILE a booking is being processed, THE App SHALL display a loading indicator and prevent duplicate submission.

---

### Requirement 5: Payment Integration

**User Story:** As a Customer, I want to pay for my booking securely, so that my ticket is confirmed.

#### Acceptance Criteria

1. THE App SHALL support payment via credit card, debit card, and at least one regional payment method suitable for the Saudi Arabia market (e.g., Mada, Apple Pay, or Tap Payments).
2. WHEN a Customer submits payment details, THE App SHALL transmit payment data exclusively to the Payment_Gateway SDK and SHALL NOT transmit raw card data to the API.
3. WHEN the Payment_Gateway confirms a successful payment, THE API SHALL update the Booking status to `ticketed` and trigger E-ticket generation.
4. WHEN the Payment_Gateway returns a payment failure, THE API SHALL retain the Booking in `pending_payment` status and THE App SHALL display the failure reason and offer a retry.
5. THE App SHALL display a payment confirmation screen with Booking ID, PNR, total amount paid, and a link to download the E-ticket.
6. THE App SHALL allow the Customer to apply Loyalty_Points as a partial payment discount during checkout.
7. WHEN Loyalty_Points are applied, THE API SHALL validate that the Customer has sufficient points and deduct them upon successful payment.

---

### Requirement 6: PNR Tracking

**User Story:** As a Customer, I want to track my PNR status, so that I can stay informed about my booking.

#### Acceptance Criteria

1. THE App SHALL provide a PNR tracking screen where a Customer can enter a PNR code to retrieve booking status.
2. WHEN a Customer submits a valid PNR, THE API SHALL retrieve the current booking status from the GDS and return itinerary details, Passenger names, ticket status, and flight status.
3. WHEN a Customer submits an invalid or non-existent PNR, THE API SHALL return a 404 error and THE App SHALL display a descriptive message.
4. THE App SHALL display PNR tracking results including flight number, route, departure and arrival times, booking status, and ticket numbers.
5. WHEN a tracked flight is delayed or cancelled, THE API SHALL reflect the updated status from the GDS in the PNR tracking response.

---

### Requirement 7: Booking History

**User Story:** As a Customer, I want to view my past and upcoming bookings, so that I can manage my travel.

#### Acceptance Criteria

1. THE App SHALL display a booking history screen listing all Bookings associated with the authenticated Customer.
2. THE App SHALL allow the Customer to filter bookings by status (upcoming, completed, cancelled).
3. WHEN a Customer taps a Booking in the list, THE App SHALL display the full Booking detail including itinerary, Passenger list, PNR, payment amount, and booking status.
4. THE API SHALL return booking history results paginated at 10 items per page.
5. WHEN a Customer has no bookings, THE App SHALL display an empty state with a prompt to search for flights.

---

### Requirement 8: E-ticket Download

**User Story:** As a Customer, I want to download my e-ticket, so that I have proof of my booking for travel.

#### Acceptance Criteria

1. WHEN a Booking has status `ticketed`, THE App SHALL display a "Download E-ticket" button on the Booking detail screen.
2. WHEN a Customer taps "Download E-ticket", THE API SHALL generate and return a PDF E-ticket containing PNR, passenger names, itinerary details, ticket numbers, and barcode.
3. THE App SHALL save the downloaded E-ticket PDF to the device's local storage and open it in the device's default PDF viewer.
4. THE App SHALL allow the Customer to share the E-ticket PDF via the device's native share sheet.
5. IF the E-ticket PDF generation fails, THEN THE API SHALL return a 500 error and THE App SHALL display a retry option.

---

### Requirement 9: Push Notifications

**User Story:** As a Customer, I want to receive push notifications, so that I am alerted to important booking and flight updates.

#### Acceptance Criteria

1. WHEN a Customer installs and opens the App for the first time, THE App SHALL request permission to send Push_Notifications.
2. WHEN a Customer grants notification permission, THE App SHALL register the device FCM token with the API.
3. THE API SHALL send a Push_Notification to the Customer's registered device when a Booking is confirmed.
4. THE API SHALL send a Push_Notification to the Customer's registered device when a Booking is cancelled.
5. THE API SHALL send a Push_Notification to the Customer's registered device when a tracked flight's status changes (delayed, cancelled, gate change).
6. THE API SHALL send a Push_Notification to the Customer's registered device when Loyalty_Points are earned or redeemed.
7. WHEN a Customer taps a Push_Notification, THE App SHALL navigate to the relevant Booking detail or PNR tracking screen.
8. THE App SHALL allow the Customer to manage notification preferences (enable/disable per notification category) from the profile settings screen.

---

### Requirement 10: Loyalty Points System

**User Story:** As a Customer, I want to earn and redeem loyalty points, so that I am rewarded for booking through Mushqila.

#### Acceptance Criteria

1. WHEN a Booking reaches `ticketed` status, THE API SHALL calculate and credit Loyalty_Points to the Customer's account based on the booking value and the active LoyaltyProgram rate.
2. THE App SHALL display the Customer's current Loyalty_Points balance and Loyalty_Tier on the profile and dashboard screens.
3. THE App SHALL display a Loyalty_Points transaction history showing earned, redeemed, and expired points with dates and associated Booking references.
4. WHEN a Customer's accumulated Loyalty_Points cross a tier upgrade threshold, THE API SHALL upgrade the Customer's Loyalty_Tier and send a Push_Notification.
5. THE App SHALL display available Rewards that the Customer can redeem using Loyalty_Points, including points required, reward type, and validity.
6. WHEN a Customer redeems a Reward, THE API SHALL deduct the required Loyalty_Points, generate a redemption code, and return the CustomerReward record.
7. IF a Customer attempts to redeem a Reward with insufficient Loyalty_Points, THEN THE API SHALL return a 400 error and THE App SHALL display the points shortfall.

---

### Requirement 11: Multi-language Support (Arabic and English)

**User Story:** As a Customer, I want to use the App in Arabic or English, so that I can navigate comfortably in my preferred language.

#### Acceptance Criteria

1. THE App SHALL support Arabic (`ar`) and English (`en`) as selectable Locale options.
2. WHEN a Customer selects a Locale, THE App SHALL apply the selected language to all UI labels, error messages, and static content immediately without requiring a restart.
3. WHILE the active Locale is Arabic, THE App SHALL render all screens in right-to-left (RTL) layout.
4. WHILE the active Locale is English, THE App SHALL render all screens in left-to-right (LTR) layout.
5. THE App SHALL persist the Customer's Locale preference and restore it on subsequent app launches.
6. WHERE a Customer is authenticated, THE API SHALL accept a `Accept-Language` header and return localizable content (e.g., error messages, airport names) in the requested language.

---

### Requirement 12: Customer Profile Management

**User Story:** As a Customer, I want to manage my profile and travel documents, so that booking is faster and my information is accurate.

#### Acceptance Criteria

1. THE App SHALL display a profile screen showing the Customer's name, email, phone number, Loyalty_Tier, and Loyalty_Points balance.
2. WHEN a Customer updates profile fields (name, phone, preferred language, preferred currency), THE API SHALL save the changes and return the updated Customer record.
3. THE App SHALL allow the Customer to add, edit, and delete passport details (passport number, expiry date, nationality) on the CustomerProfile.
4. THE App SHALL allow the Customer to add, edit, and delete TravelCompanion records (name, relationship, date of birth, passport details).
5. WHEN a Customer uploads a profile photo, THE API SHALL store the image and return the updated profile image URL.
6. IF a Customer attempts to save a passport with an expiry date in the past, THEN THE App SHALL display a validation error before submitting to the API.

---

### Requirement 13: API Authentication and Security

**User Story:** As the platform operator, I want all mobile API communication to be authenticated and secure, so that customer data is protected.

#### Acceptance Criteria

1. THE API SHALL require a valid Auth_Token on all endpoints except registration, login, and public flight search.
2. THE API SHALL issue JWT tokens with a 24-hour expiry and support a refresh token flow with a 30-day refresh window.
3. THE App SHALL transmit all API requests over HTTPS.
4. THE API SHALL rate-limit unauthenticated endpoints to 60 requests per minute per IP address.
5. THE API SHALL rate-limit authenticated endpoints to 300 requests per minute per Customer.
6. IF an Auth_Token is used from an unrecognized device after a password change, THEN THE API SHALL invalidate the token and return a 401 error.

---

### Requirement 14: New Django API Endpoints

**User Story:** As a mobile developer, I want dedicated REST API endpoints for the Flutter app, so that the app can consume all required data.

#### Acceptance Criteria

1. THE API SHALL expose a `/api/v1/` prefix for all mobile-facing endpoints, separate from existing web views.
2. THE API SHALL provide endpoints for: customer registration, login, token refresh, logout, profile read/update, password change, OTP verification, flight search, booking creation, booking list, booking detail, PNR tracking, e-ticket download, loyalty points balance, loyalty transaction history, reward list, reward redemption, push notification token registration, and notification preference update.
3. THE API SHALL return all responses in JSON format with a consistent envelope: `{"success": true/false, "data": {...}, "error": null/"message"}`.
4. THE API SHALL version all endpoints under `/api/v1/` to allow future non-breaking evolution.
5. WHEN the API receives a request with an `Accept-Language: ar` header, THE API SHALL return localizable string fields in Arabic where translations are available.
