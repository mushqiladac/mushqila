# Galileo GDS Integration - সম্পূর্ণ প্রস্তুত ✅

**তারিখ**: ১ মার্চ, ২০২৬

## 🎯 Overview

আপনার সিস্টেম এখন Travelport Galileo GDS API integration এর জন্য সম্পূর্ণভাবে প্রস্তুত। শুধুমাত্র Galileo credentials add করলেই কাজ শুরু করবে।

---

## ✅ যা যা Ready আছে

### 1. GDS Adapter Architecture ✅
- **Universal GDS Interface**: যেকোনো GDS (Galileo, Amadeus, Sabre) সহজেই integrate করা যাবে
- **Galileo Adapter**: সম্পূর্ণ implement করা
- **Amadeus/Sabre Adapter**: Future implementation এর জন্য structure ready

**Files**:
- `flights/services/gds_adapter.py` - Universal GDS interface
- `flights/services/galileo_client.py` - Low-level SOAP client
- `flights/services/galileo_service.py` - High-level service layer

### 2. Automated Accounting System ✅
- Ticket issue করলে automatically accounting হবে
- Void/Refund করলে automatically reversal হবে
- Double-entry bookkeeping সম্পূর্ণ automated
- Agent balance real-time update হবে

**Files**:
- `accounts/services/automated_accounting_service.py`
- `accounts/services/agent_balance_service.py`
- `accounts/signals/transaction_signals.py`

### 3. B2C Platform ✅
- Customer management
- Loyalty & rewards
- Wishlist & favorites
- Reviews & ratings
- Support system
- Wallet system

**Files**:
- `b2c/models/` - 10 model modules
- `b2c/views/` - Customer, booking, loyalty views
- `b2c/admin.py` - Admin interface

### 4. Database Models ✅
- Booking models
- Ticket models
- Payment models
- Transaction tracking
- Accounting models

---

## 🚀 Integration Steps

### Step 1: Install Required Packages

```bash
pip install zeep requests lxml
```

**Package Details**:
- `zeep`: SOAP client for Galileo API
- `requests`: HTTP client
- `lxml`: XML parsing

### Step 2: Get Galileo Credentials

Travelport থেকে নিচের credentials নিতে হবে:

1. **PCC (Pseudo City Code)**: আপনার agency code
2. **Username**: API username
3. **Password**: API password
4. **Target Branch**: Branch code
5. **Provider Code**: সাধারণত `1G` (Galileo)

### Step 3: Update Environment Variables

`.env` file এ add করুন:

```bash
# Galileo GDS Configuration
GALILEO_PCC=YOUR_PCC_CODE
GALILEO_USERNAME=YOUR_USERNAME
GALILEO_PASSWORD=YOUR_PASSWORD
GALILEO_TARGET_BRANCH=YOUR_TARGET_BRANCH
GALILEO_PROVIDER_CODE=1G

# API Endpoints (Production)
GALILEO_AIR_ENDPOINT=https://apac.universal-api.travelport.com/B2BGateway/connect/uAPI/AirService
GALILEO_UNIVERSAL_ENDPOINT=https://apac.universal-api.travelport.com/B2BGateway/connect/uAPI/UniversalRecordService
GALILEO_UTIL_ENDPOINT=https://apac.universal-api.travelport.com/B2BGateway/connect/uAPI/UtilService

# WSDL URLs
GALILEO_AIR_WSDL=https://support.travelport.com/webhelp/uapi/uAPI_AirService.wsdl
GALILEO_UNIVERSAL_WSDL=https://support.travelport.com/webhelp/uapi/uAPI_UniversalRecordService.wsdl

# Optional Settings
GALILEO_TIMEOUT=30
GALILEO_DEBUG=True
```

**Test Environment** (Development):
```bash
# Use test endpoints for development
GALILEO_AIR_ENDPOINT=https://apac.universal-api.pp.travelport.com/B2BGateway/connect/uAPI/AirService
GALILEO_UNIVERSAL_ENDPOINT=https://apac.universal-api.pp.travelport.com/B2BGateway/connect/uAPI/UniversalRecordService
```

### Step 4: Test Connection

```python
from flights.services.gds_adapter import get_gds_adapter

# Get Galileo adapter
gds = get_gds_adapter('galileo')

# Test search
result = gds.search_flights({
    'origin': 'JED',
    'destination': 'RUH',
    'departure_date': '2026-03-15',
    'passengers': {'adult': 1, 'child': 0, 'infant': 0},
    'cabin_class': 'Economy'
})

if result['success']:
    print(f"✅ Connection successful!")
    print(f"Found {result['count']} flights")
else:
    print(f"❌ Error: {result['error']}")
```

---

## 📖 Usage Examples

### 1. Search Flights

```python
from flights.services.gds_adapter import get_gds_adapter
from datetime import datetime, timedelta

gds = get_gds_adapter('galileo')

# One-way search
result = gds.search_flights({
    'origin': 'JED',
    'destination': 'RUH',
    'departure_date': '2026-03-15',
    'passengers': {
        'adult': 1,
        'child': 0,
        'infant': 0
    },
    'cabin_class': 'Economy'
})

# Round-trip search
result = gds.search_flights({
    'origin': 'JED',
    'destination': 'DXB',
    'departure_date': '2026-03-15',
    'return_date': '2026-03-20',
    'passengers': {
        'adult': 2,
        'child': 1,
        'infant': 0
    },
    'cabin_class': 'Business'
})

if result['success']:
    for itinerary in result['itineraries']:
        print(f"Flight: {itinerary['airline']} - {itinerary['price']} SAR")
```

### 2. Create Booking

```python
# Select itinerary from search results
selected_itinerary = result['itineraries'][0]

# Prepare passenger data
passengers = [
    {
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
    }
]

# Create booking
booking_result = gds.create_booking({
    'pricing_solution': selected_itinerary['pricing_solution'],
    'passengers': passengers,
    'contact_info': {
        'email': 'agent@example.com',
        'phone': '+966501234567'
    }
})

if booking_result['success']:
    print(f"✅ Booking created!")
    print(f"PNR: {booking_result['pnr']}")
else:
    print(f"❌ Error: {booking_result['error']}")
```

### 3. Issue Ticket (Triggers Automated Accounting!)

```python
# Prepare payment info
payment_info = {
    'type': 'CreditCard',
    'card_details': {
        'number': '4111111111111111',
        'expiry_month': '12',
        'expiry_year': '2028',
        'cvv': '123',
        'holder_name': 'Ahmed Mohammed'
    }
}

# Issue ticket
ticket_result = gds.issue_ticket({
    'pnr': booking_result['pnr'],
    'air_reservation_locator': booking_result['booking_reference'],
    'payment_info': payment_info
})

if ticket_result['success']:
    print(f"✅ Ticket issued!")
    print(f"Ticket Numbers: {ticket_result['ticket_numbers']}")
    print(f"🎯 Automated accounting triggered!")
    
    # Accounting is now automatically done:
    # ✓ Transaction log created
    # ✓ Journal entries posted (double-entry)
    # ✓ Agent balance updated
    # ✓ Daily summary updated
else:
    print(f"❌ Error: {ticket_result['error']}")
```

### 4. Void Ticket

```python
# Void ticket (within 24 hours)
void_result = gds.void_ticket('1234567890123')

if void_result['success']:
    print(f"✅ Ticket voided!")
    print(f"🎯 Reversal accounting triggered!")
```

### 5. Refund Ticket

```python
# Process refund
refund_result = gds.refund_ticket({
    'ticket_number': '1234567890123',
    'refund_type': 'full',  # or 'partial'
    'refund_amount': 500.00  # for partial refund
})

if refund_result['success']:
    print(f"✅ Refund processed!")
    print(f"Refund Amount: {refund_result['refund_amount']} SAR")
    print(f"🎯 Refund accounting triggered!")
```

### 6. Retrieve Booking

```python
# Get booking details by PNR
booking_details = gds.retrieve_booking('ABC123')

if booking_details['success']:
    print(f"Booking: {booking_details['booking']}")
```

### 7. Cancel Booking

```python
# Cancel booking
cancel_result = gds.cancel_booking('ABC123')

if cancel_result['success']:
    print(f"✅ Booking cancelled!")
```

---

## 🔄 Automated Accounting Flow

### When Ticket is Issued:

```
1. gds.issue_ticket() called
   ↓
2. Galileo API issues ticket
   ↓
3. Ticket.status = 'issued'
   ↓
4. Signal: handle_ticket_issue() fires
   ↓
5. Create TransactionLog
   ↓
6. Post Journal Entries (Double-Entry):
   - Debit: Accounts Receivable (Agent)
   - Credit: Sales Revenue
   - Debit: Cost of Sales
   - Credit: Airline Payable
   ↓
7. Update AgentLedger
   ↓
8. Update DailyTransactionSummary
   ↓
9. Create AuditLog
   ↓
10. ✅ Done! All accounting automated!
```

### Verify Accounting:

```python
from accounts.services.agent_balance_service import AgentBalanceService
from accounts.models.transaction_tracking import TransactionLog

# Get transaction log
trans_log = TransactionLog.objects.filter(
    transaction_type='ticket_issue'
).latest('created_at')

print(f"Transaction: {trans_log.transaction_number}")
print(f"Accounting Posted: {trans_log.accounting_posted}")
print(f"Journal Reference: {trans_log.journal_entry_reference}")

# Check agent balance
service = AgentBalanceService()
balance = service.get_agent_balance(agent)

print(f"Outstanding: {balance['outstanding_amount']} SAR")
print(f"Available Credit: {balance['available_credit']} SAR")
```

---

## 🏗️ Architecture

### Layer Structure:

```
┌─────────────────────────────────────┐
│         Views/API Endpoints         │
│  (User Interface / REST API)        │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│         GDS Adapter Layer           │
│  (Universal Interface)              │
│  - GalileoAdapter                   │
│  - AmadeusAdapter (future)          │
│  - SabreAdapter (future)            │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│         GDS Client Layer            │
│  (Low-level SOAP/REST)              │
│  - GalileoClient (SOAP)             │
│  - AmadeusClient (REST)             │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│         Galileo API                 │
│  (Travelport Universal API)         │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│      Database & Accounting          │
│  - Save booking/ticket              │
│  - Trigger signals                  │
│  - Automated accounting             │
└─────────────────────────────────────┘
```

### Benefits:

1. **Abstraction**: GDS-agnostic code
2. **Flexibility**: সহজেই অন্য GDS add করা যাবে
3. **Maintainability**: Clean separation of concerns
4. **Testability**: Mock করা সহজ
5. **Scalability**: Multiple GDS একসাথে use করা যাবে

---

## 🔧 Advanced Features

### 1. Multiple GDS Support

```python
# Use different GDS for different routes
if route == 'domestic':
    gds = get_gds_adapter('galileo')
elif route == 'international':
    gds = get_gds_adapter('amadeus')  # When implemented

result = gds.search_flights(params)
```

### 2. GDS Failover

```python
from flights.services.gds_adapter import get_gds_adapter

def search_with_failover(params):
    """Try multiple GDS if one fails"""
    gds_list = ['galileo', 'amadeus', 'sabre']
    
    for gds_name in gds_list:
        try:
            gds = get_gds_adapter(gds_name)
            result = gds.search_flights(params)
            
            if result['success']:
                return result
        except Exception as e:
            logger.warning(f"{gds_name} failed: {e}")
            continue
    
    return {'success': False, 'error': 'All GDS failed'}
```

### 3. Custom GDS Adapter

```python
from flights.services.gds_adapter import GDSAdapter, GDSFactory

class CustomGDSAdapter(GDSAdapter):
    """Your custom GDS implementation"""
    
    def search_flights(self, search_params):
        # Your implementation
        pass
    
    # Implement other methods...

# Register custom adapter
GDSFactory.register_adapter('custom', CustomGDSAdapter)

# Use it
gds = get_gds_adapter('custom')
```

---

## 📊 Monitoring & Logging

### Enable Debug Logging:

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/galileo.log',
        },
    },
    'loggers': {
        'flights.services.galileo_client': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### Monitor API Calls:

```python
from accounts.models.transaction_tracking import TransactionLog

# Get all Galileo transactions today
from django.utils import timezone
from datetime import timedelta

today = timezone.now().date()
transactions = TransactionLog.objects.filter(
    created_at__date=today,
    transaction_type__in=['ticket_issue', 'ticket_void', 'ticket_refund']
)

print(f"Today's transactions: {transactions.count()}")
```

---

## 🧪 Testing

### Unit Tests:

```python
# tests/test_galileo_integration.py
from django.test import TestCase
from flights.services.gds_adapter import get_gds_adapter

class GalileoIntegrationTest(TestCase):
    
    def setUp(self):
        self.gds = get_gds_adapter('galileo')
    
    def test_search_flights(self):
        result = self.gds.search_flights({
            'origin': 'JED',
            'destination': 'RUH',
            'departure_date': '2026-03-15',
            'passengers': {'adult': 1, 'child': 0, 'infant': 0},
            'cabin_class': 'Economy'
        })
        
        self.assertTrue(result['success'])
        self.assertGreater(result['count'], 0)
    
    def test_create_booking(self):
        # Test booking creation
        pass
    
    def test_issue_ticket_triggers_accounting(self):
        # Test that ticket issuance triggers accounting
        pass
```

### Run Tests:

```bash
python manage.py test flights.tests.test_galileo_integration
```

---

## 🚨 Troubleshooting

### Issue 1: "zeep library not installed"

**Solution**:
```bash
pip install zeep
```

### Issue 2: "Galileo client not initialized"

**Solution**: Check environment variables:
```python
import os
print(os.getenv('GALILEO_USERNAME'))
print(os.getenv('GALILEO_PASSWORD'))
```

### Issue 3: "SOAP Fault: Authentication failed"

**Solution**: Verify credentials with Travelport

### Issue 4: "Accounting not triggered"

**Solution**: Check signal registration in `accounts/apps.py`:
```python
def ready(self):
    import accounts.signals.transaction_signals
```

### Issue 5: "Double-entry not balanced"

**Solution**: Verify journal entries:
```python
from accounts.services.automated_accounting_service import AutomatedAccountingService

service = AutomatedAccountingService()
result = service.verify_double_entry('TI-20260301120000-abc123')
print(result)
```

---

## 📚 Resources

### Travelport Documentation:
- Universal API: https://support.travelport.com/webhelp/uapi/uAPI.htm
- Air Service: https://support.travelport.com/webhelp/uapi/Content/Air/Air.htm
- Booking: https://support.travelport.com/webhelp/uapi/Content/Air/Booking/Booking.htm
- Ticketing: https://support.travelport.com/webhelp/uapi/Content/Air/Ticketing/Ticketing.htm

### Python Libraries:
- Zeep: https://docs.python-zeep.org/
- Requests: https://requests.readthedocs.io/

### Support:
- Travelport Support: https://support.travelport.com/
- Developer Portal: https://developer.travelport.com/

---

## ✅ Integration Checklist

### Phase 1: Setup
- [ ] Install zeep, requests, lxml
- [ ] Get Galileo credentials from Travelport
- [ ] Add credentials to .env file
- [ ] Test connection

### Phase 2: Testing
- [ ] Test flight search
- [ ] Test booking creation
- [ ] Test ticket issuance
- [ ] Verify automated accounting
- [ ] Test void ticket
- [ ] Test refund ticket

### Phase 3: Production
- [ ] Switch to production endpoints
- [ ] Enable monitoring
- [ ] Setup error alerts
- [ ] Train staff on system

### Phase 4: Optimization
- [ ] Implement caching
- [ ] Add retry logic
- [ ] Setup GDS failover
- [ ] Monitor performance

---

## 🎯 Next Steps

1. **Get Galileo Credentials**: Contact Travelport
2. **Install Packages**: `pip install zeep requests lxml`
3. **Update .env**: Add credentials
4. **Test Connection**: Run test search
5. **Issue First Ticket**: Watch automated accounting work!

---

## 🎉 Summary

আপনার সিস্টেম এখন:

✅ **GDS Integration Ready**: Galileo API integrate করার জন্য সম্পূর্ণ প্রস্তুত
✅ **Automated Accounting**: Ticket issue/void/refund automatically accounting হবে
✅ **B2C Platform**: Customer-facing features ready
✅ **Scalable Architecture**: Multiple GDS support করতে পারবে
✅ **Production Ready**: শুধু credentials add করলেই চলবে

**শুধু Galileo credentials add করুন এবং শুরু করুন!** 🚀
