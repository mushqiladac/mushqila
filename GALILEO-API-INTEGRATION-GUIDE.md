# Galileo GDS API Integration Guide

**তারিখ**: ২৬ জানুয়ারি, ২০২৬

## Overview

এই guide আপনাকে step-by-step Galileo GDS API integrate করতে সাহায্য করবে। Integration complete হলে automated accounting system automatically কাজ করবে।

---

## Prerequisites

### 1. Galileo Credentials প্রয়োজন:
- ✓ PCC (Pseudo City Code)
- ✓ Username
- ✓ Password
- ✓ API Endpoint URL
- ✓ WSDL URLs (for SOAP services)

### 2. Environment Variables Setup

`.env` file এ add করুন:

```bash
# Galileo GDS Configuration
GALILEO_PCC=YOUR_PCC_CODE
GALILEO_USERNAME=YOUR_USERNAME
GALILEO_PASSWORD=YOUR_PASSWORD
GALILEO_ENDPOINT=https://apac.universal-api.travelport.com/B2BGateway/connect/uAPI/AirService
GALILEO_TARGET_BRANCH=YOUR_TARGET_BRANCH

# Optional
GALILEO_TIMEOUT=30
GALILEO_DEBUG=True
```

---

## Step 1: Update Galileo Service

File: `flights/services/galileo_service.py`

### Current Status:
- ✓ Basic structure আছে
- ⏳ API calls implement করতে হবে

### Implementation:

```python
# flights/services/galileo_service.py
import os
import requests
from decimal import Decimal
from datetime import datetime, timedelta
from django.conf import settings
from zeep import Client
from zeep.transports import Transport
from requests import Session

class GalileoService:
    """
    Galileo GDS API Integration Service
    Handles flight search, booking, ticketing via Travelport Universal API
    """
    
    def __init__(self):
        self.pcc = os.getenv('GALILEO_PCC')
        self.username = os.getenv('GALILEO_USERNAME')
        self.password = os.getenv('GALILEO_PASSWORD')
        self.endpoint = os.getenv('GALILEO_ENDPOINT')
        self.target_branch = os.getenv('GALILEO_TARGET_BRANCH')
        
        # Setup SOAP client
        session = Session()
        session.auth = (self.username, self.password)
        transport = Transport(session=session)
        
        # Air Service WSDL
        self.air_client = Client(
            'https://support.travelport.com/webhelp/uapi/uAPI.htm',
            transport=transport
        )
    
    def search_flights(self, origin, destination, departure_date, 
                      return_date=None, adults=1, children=0, infants=0,
                      cabin_class='Y'):
        """
        Search flights using Galileo API
        
        Args:
            origin: Airport IATA code (e.g., 'JED')
            destination: Airport IATA code (e.g., 'RUH')
            departure_date: Date object
            return_date: Date object (for round trip)
            adults: Number of adults
            children: Number of children
            infants: Number of infants
            cabin_class: Y/W/C/F
        
        Returns:
            List of flight itineraries with pricing
        """
        try:
            # Build search request
            search_request = {
                'BillingPointOfSaleInfo': {
                    'OriginApplication': 'UAPI'
                },
                'SearchAirLeg': [
                    {
                        'SearchOrigin': [{'Airport': {'Code': origin}}],
                        'SearchDestination': [{'Airport': {'Code': destination}}],
                        'SearchDepTime': departure_date.strftime('%Y-%m-%d'),
                    }
                ],
                'AirSearchModifiers': {
                    'PreferredCabins': [{'CabinClass': cabin_class}]
                },
                'SearchPassenger': []
            }
            
            # Add passengers
            for i in range(adults):
                search_request['SearchPassenger'].append({
                    'Code': 'ADT',
                    'Age': 30
                })
            
            for i in range(children):
                search_request['SearchPassenger'].append({
                    'Code': 'CNN',
                    'Age': 10
                })
            
            for i in range(infants):
                search_request['SearchPassenger'].append({
                    'Code': 'INF',
                    'Age': 1
                })
            
            # Add return leg if round trip
            if return_date:
                search_request['SearchAirLeg'].append({
                    'SearchOrigin': [{'Airport': {'Code': destination}}],
                    'SearchDestination': [{'Airport': {'Code': origin}}],
                    'SearchDepTime': return_date.strftime('%Y-%m-%d'),
                })
            
            # Call Galileo API
            response = self.air_client.service.LowFareSearchReq(**search_request)
            
            # Parse response
            itineraries = self._parse_search_response(response)
            
            return {
                'success': True,
                'itineraries': itineraries,
                'count': len(itineraries)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_booking(self, itinerary_data, passengers, agent):
        """
        Create booking/PNR in Galileo
        
        Args:
            itinerary_data: Selected flight itinerary
            passengers: List of passenger data
            agent: Agent user object
        
        Returns:
            PNR details
        """
        try:
            # Build booking request
            booking_request = {
                'BillingPointOfSaleInfo': {
                    'OriginApplication': 'UAPI'
                },
                'BookingTraveler': [],
                'AirPricingSolution': itinerary_data['pricing_solution'],
                'ActionStatus': {
                    'Type': 'TAW',  # Ticketing Arrangement
                    'TicketDate': (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d'),
                    'ProviderCode': '1G'
                }
            }
            
            # Add travelers
            for idx, passenger in enumerate(passengers):
                traveler = {
                    'Key': f'Traveler_{idx}',
                    'TravelerType': passenger['type'],  # ADT/CNN/INF
                    'BookingTravelerName': {
                        'Prefix': passenger['title'],
                        'First': passenger['first_name'],
                        'Last': passenger['last_name']
                    },
                    'DOB': passenger['date_of_birth'].strftime('%Y-%m-%d'),
                    'Gender': passenger['gender'],
                    'PhoneNumber': [{
                        'Type': 'Mobile',
                        'Number': passenger.get('phone', '')
                    }],
                    'Email': [{
                        'Type': 'Primary',
                        'EmailID': passenger.get('email', '')
                    }],
                    'SSR': []  # Special Service Requests
                }
                
                # Add passport info if available
                if passenger.get('passport_number'):
                    traveler['SSR'].append({
                        'Type': 'DOCS',
                        'FreeText': f"P/{passenger['nationality']}/{passenger['passport_number']}"
                                   f"/{passenger['nationality']}/{passenger['date_of_birth'].strftime('%d%b%y')}"
                                   f"/{passenger['gender']}/{passenger['passport_expiry'].strftime('%d%b%y')}"
                                   f"/{passenger['last_name']}/{passenger['first_name']}"
                    })
                
                booking_request['BookingTraveler'].append(traveler)
            
            # Call Galileo API
            response = self.air_client.service.AirCreateReservationReq(**booking_request)
            
            # Parse response
            pnr_data = self._parse_booking_response(response)
            
            return {
                'success': True,
                'pnr': pnr_data['locator_code'],
                'booking_data': pnr_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def issue_ticket(self, pnr, payment_info):
        """
        Issue ticket in Galileo
        
        THIS IS THE KEY METHOD - When ticket is issued, 
        automated accounting signals will trigger automatically!
        
        Args:
            pnr: PNR locator code
            payment_info: Payment details
        
        Returns:
            Ticket numbers and details
        """
        try:
            # Build ticketing request
            ticket_request = {
                'BillingPointOfSaleInfo': {
                    'OriginApplication': 'UAPI'
                },
                'AirReservationLocatorCode': pnr,
                'FormOfPayment': {
                    'Type': payment_info['type'],  # Cash/Credit/Check
                    'CreditCard': payment_info.get('card_details') if payment_info['type'] == 'Credit' else None
                },
                'Commission': {
                    'Type': 'PercentBase',
                    'Value': '10.00'  # 10% commission
                }
            }
            
            # Call Galileo API
            response = self.air_client.service.AirTicketingReq(**ticket_request)
            
            # Parse response
            ticket_data = self._parse_ticket_response(response)
            
            # IMPORTANT: Update ticket status in database
            # This will trigger automated accounting signals!
            from flights.models.booking_models import Ticket
            from django.utils import timezone
            
            for ticket_info in ticket_data['tickets']:
                ticket = Ticket.objects.get(ticket_number=ticket_info['number'])
                ticket.status = 'issued'  # ← THIS TRIGGERS AUTOMATED ACCOUNTING!
                ticket.issue_date = timezone.now()
                ticket.save()
            
            return {
                'success': True,
                'tickets': ticket_data['tickets']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def void_ticket(self, ticket_number):
        """
        Void ticket in Galileo
        
        Args:
            ticket_number: Ticket number to void
        
        Returns:
            Void confirmation
        """
        try:
            # Build void request
            void_request = {
                'BillingPointOfSaleInfo': {
                    'OriginApplication': 'UAPI'
                },
                'AirTicketNumber': ticket_number,
                'ProviderCode': '1G'
            }
            
            # Call Galileo API
            response = self.air_client.service.AirVoidDocumentReq(**void_request)
            
            # Update ticket status - triggers automated accounting!
            from flights.models.booking_models import Ticket
            from django.utils import timezone
            
            ticket = Ticket.objects.get(ticket_number=ticket_number)
            ticket.status = 'voided'  # ← THIS TRIGGERS VOID ACCOUNTING!
            ticket.void_date = timezone.now()
            ticket.save()
            
            return {
                'success': True,
                'message': 'Ticket voided successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def refund_ticket(self, ticket_number, refund_type='full'):
        """
        Process ticket refund in Galileo
        
        Args:
            ticket_number: Ticket number to refund
            refund_type: 'full' or 'partial'
        
        Returns:
            Refund confirmation
        """
        try:
            # Build refund request
            refund_request = {
                'BillingPointOfSaleInfo': {
                    'OriginApplication': 'UAPI'
                },
                'AirTicketNumber': ticket_number,
                'RefundType': refund_type.upper(),
                'ProviderCode': '1G'
            }
            
            # Call Galileo API
            response = self.air_client.service.AirRefundReq(**refund_request)
            
            # Parse refund response
            refund_data = self._parse_refund_response(response)
            
            # Update ticket status - triggers automated accounting!
            from flights.models.booking_models import Ticket
            from django.utils import timezone
            
            ticket = Ticket.objects.get(ticket_number=ticket_number)
            ticket.status = 'refunded'  # ← THIS TRIGGERS REFUND ACCOUNTING!
            ticket.refund_date = timezone.now()
            ticket.save()
            
            return {
                'success': True,
                'refund_amount': refund_data['amount'],
                'penalty': refund_data['penalty']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # Helper methods for parsing responses
    def _parse_search_response(self, response):
        """Parse Galileo search response"""
        # Implementation depends on Galileo response structure
        pass
    
    def _parse_booking_response(self, response):
        """Parse Galileo booking response"""
        pass
    
    def _parse_ticket_response(self, response):
        """Parse Galileo ticketing response"""
        pass
    
    def _parse_refund_response(self, response):
        """Parse Galileo refund response"""
        pass
```

---

## Step 2: Update Views

File: `flights/views/booking_views.py`

```python
from flights.services.galileo_service import GalileoService

def issue_ticket_view(request, booking_id):
    """
    Issue ticket - This will trigger automated accounting!
    """
    booking = get_object_or_404(Booking, id=booking_id, agent=request.user)
    
    # Initialize Galileo service
    galileo = GalileoService()
    
    # Prepare payment info
    payment_info = {
        'type': 'Credit',
        'card_details': {
            # Card details from payment form
        }
    }
    
    # Issue ticket via Galileo
    result = galileo.issue_ticket(booking.pnr, payment_info)
    
    if result['success']:
        # Tickets are now issued!
        # Automated accounting has already been triggered by the signal!
        
        messages.success(request, 'Ticket issued successfully!')
        messages.info(request, 'Accounting entries posted automatically.')
        
        return redirect('booking_detail', booking_id=booking.id)
    else:
        messages.error(request, f'Error: {result["error"]}')
        return redirect('booking_detail', booking_id=booking.id)
```

---

## Step 3: Testing Flow

### 1. Search Flights
```python
from flights.services.galileo_service import GalileoService

galileo = GalileoService()

# Search
result = galileo.search_flights(
    origin='JED',
    destination='RUH',
    departure_date=datetime(2026, 3, 1).date(),
    adults=1,
    cabin_class='Y'
)

print(f"Found {result['count']} flights")
```

### 2. Create Booking
```python
# Select itinerary
selected_itinerary = result['itineraries'][0]

# Prepare passenger data
passengers = [{
    'type': 'ADT',
    'title': 'MR',
    'first_name': 'Ahmed',
    'last_name': 'Mohammed',
    'date_of_birth': datetime(1990, 1, 1).date(),
    'gender': 'M',
    'nationality': 'SA',
    'passport_number': 'A12345678',
    'passport_expiry': datetime(2028, 1, 1).date(),
    'email': 'ahmed@example.com',
    'phone': '+966501234567'
}]

# Create booking
booking_result = galileo.create_booking(
    selected_itinerary,
    passengers,
    agent
)

print(f"PNR: {booking_result['pnr']}")
```

### 3. Issue Ticket (Triggers Automated Accounting!)
```python
# Prepare payment
payment_info = {
    'type': 'Credit',
    'card_details': {
        'number': '4111111111111111',
        'expiry': '12/28',
        'cvv': '123'
    }
}

# Issue ticket
ticket_result = galileo.issue_ticket(
    booking_result['pnr'],
    payment_info
)

# ✓ Ticket issued
# ✓ Automated accounting triggered!
# ✓ Transaction log created
# ✓ Journal entries posted
# ✓ Agent balance updated
# ✓ Daily summary updated

print("Ticket issued and accounting completed automatically!")
```

---

## Step 4: Verify Automated Accounting

After issuing ticket, verify:

```python
from accounts.services.agent_balance_service import AgentBalanceService
from accounts.models.transaction_tracking import TransactionLog
from accounts.models.accounting import JournalEntry

# Check transaction log
trans_log = TransactionLog.objects.filter(
    agent=agent,
    transaction_type='ticket_issue'
).latest('created_at')

print(f"Transaction: {trans_log.transaction_number}")
print(f"Accounting Posted: {trans_log.accounting_posted}")
print(f"Journal Reference: {trans_log.journal_entry_reference}")

# Check journal entries
entries = JournalEntry.objects.filter(
    reference_number=trans_log.journal_entry_reference
)

for entry in entries:
    print(f"{entry.account.code}: {entry.entry_type} {entry.amount}")

# Check agent balance
service = AgentBalanceService()
balance = service.get_agent_balance(agent)

print(f"Outstanding: {balance['outstanding_amount']} SAR")
print(f"Available Credit: {balance['available_credit']} SAR")
```

---

## Step 5: Complete Integration Checklist

### Phase 1: Setup ✓
- [ ] Get Galileo credentials
- [ ] Add environment variables
- [ ] Install required packages: `pip install zeep requests`

### Phase 2: Implementation
- [ ] Update `galileo_service.py` with API calls
- [ ] Implement `search_flights()`
- [ ] Implement `create_booking()`
- [ ] Implement `issue_ticket()` ← **Most Important!**
- [ ] Implement `void_ticket()`
- [ ] Implement `refund_ticket()`

### Phase 3: Views & URLs
- [ ] Create search view
- [ ] Create booking view
- [ ] Create ticketing view
- [ ] Create void view
- [ ] Create refund view

### Phase 4: Testing
- [ ] Test flight search
- [ ] Test booking creation
- [ ] Test ticket issuance → **Verify automated accounting!**
- [ ] Test ticket void → **Verify reversal accounting!**
- [ ] Test ticket refund → **Verify refund accounting!**

### Phase 5: Verification
- [ ] Check TransactionLog created
- [ ] Check JournalEntry posted (debits = credits)
- [ ] Check AgentLedger updated
- [ ] Check DailyTransactionSummary updated
- [ ] Check agent balance correct

---

## Important Notes

### 🔥 Key Point: Automated Accounting Triggers

Automated accounting triggers হয় যখন:

```python
# Ticket Issue
ticket.status = 'issued'
ticket.issue_date = timezone.now()
ticket.save()  # ← Signal triggers here!

# Ticket Void
ticket.status = 'voided'
ticket.void_date = timezone.now()
ticket.save()  # ← Signal triggers here!

# Ticket Refund
ticket.status = 'refunded'
ticket.refund_date = timezone.now()
ticket.save()  # ← Signal triggers here!

# Payment Received
payment.status = 'captured'
payment.captured_at = timezone.now()
payment.save()  # ← Signal triggers here!
```

### Signal Flow:
```
Ticket.save()
    ↓
Signal: handle_ticket_issue()
    ↓
Create TransactionLog
    ↓
Post to Accounting (Double-Entry)
    ↓
Update Agent Ledger
    ↓
Update Daily Summary
    ↓
Create Audit Log
```

---

## Troubleshooting

### Issue: Signals not firing
**Solution**: Check `accounts/apps.py`:
```python
def ready(self):
    import accounts.signals.transaction_signals
```

### Issue: Accounting not balanced
**Solution**: Verify double-entry:
```python
from accounts.services.automated_accounting_service import AutomatedAccountingService

service = AutomatedAccountingService()
result = service.verify_double_entry('TI-20260126120000-abc123')
print(result)  # Should show debits = credits
```

### Issue: Balance not updating
**Solution**: Check signal registration and transaction status

---

## Demo Data Management

### Delete Demo Data:
```bash
# In Docker
docker-compose exec web python manage.py delete_demo_data --confirm

# Or locally
python manage.py delete_demo_data
```

### Re-initialize Chart of Accounts:
```bash
python manage.py initialize_accounts
```

---

## Resources

### Travelport Universal API Documentation:
- https://support.travelport.com/webhelp/uapi/uAPI.htm
- Air Service: https://support.travelport.com/webhelp/uapi/Content/Air/Air.htm
- Booking: https://support.travelport.com/webhelp/uapi/Content/Air/Booking/Booking.htm
- Ticketing: https://support.travelport.com/webhelp/uapi/Content/Air/Ticketing/Ticketing.htm

### Python Libraries:
- Zeep (SOAP client): https://docs.python-zeep.org/
- Requests: https://requests.readthedocs.io/

---

## Support

যদি কোন সমস্যা হয়:
1. Check Galileo API logs
2. Check Django logs for signal errors
3. Verify transaction log status
4. Check journal entries balanced
5. Use `verify_double_entry()` method

---

**Status**: Ready for Galileo API Integration
**Next Step**: Get Galileo credentials and start implementation
**Automated Accounting**: ✅ Ready and waiting!
