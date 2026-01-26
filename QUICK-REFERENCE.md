# Quick Reference - Mushqila B2B Platform

## Demo Data Management

### Delete All Demo Data
```bash
# With confirmation prompt
docker-compose exec web python manage.py delete_demo_data

# Without prompt (auto-confirm)
docker-compose exec web python manage.py delete_demo_data --confirm
```

### Initialize Chart of Accounts
```bash
docker-compose exec web python manage.py initialize_accounts
```

---

## Database Commands

### Create Migrations
```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py makemigrations accounts
docker-compose exec web python manage.py makemigrations flights
```

### Run Migrations
```bash
docker-compose exec web python manage.py migrate
```

### Reset Database (DANGER!)
```bash
docker-compose exec web python manage.py flush --no-input
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py initialize_accounts
```

---

## Docker Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f web
```

### Restart Web Service
```bash
docker-compose restart web
```

### Shell Access
```bash
docker-compose exec web python manage.py shell
```

### Create Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

---

## Testing Commands

### Run Tests
```bash
docker-compose exec web python manage.py test
```

### Check for Issues
```bash
docker-compose exec web python manage.py check
```

### Collect Static Files
```bash
docker-compose exec web python manage.py collectstatic --no-input
```

---

## Accounting System Commands

### Check Agent Balance
```python
from accounts.services.agent_balance_service import AgentBalanceService
from django.contrib.auth import get_user_model

User = get_user_model()
agent = User.objects.get(email='agent@example.com')

service = AgentBalanceService()
balance = service.get_agent_balance(agent)
print(balance)
```

### Get Outstanding Details
```python
outstanding = service.get_outstanding_details(agent)
print(f"Total Outstanding: {outstanding['total_outstanding']}")
print(f"Aging Analysis: {outstanding['aging_summary']}")
```

### Record Payment
```python
from decimal import Decimal

result = service.record_payment(
    agent=agent,
    amount=Decimal('10000.00'),
    payment_method='bank_transfer',
    reference='TRF20260126001',
    notes='Payment for January bookings'
)
print(result)
```

### Verify Double-Entry
```python
from accounts.services.automated_accounting_service import AutomatedAccountingService

service = AutomatedAccountingService()
result = service.verify_double_entry('TI-20260126120000-abc123')
print(f"Balanced: {result['balanced']}")
print(f"Debits: {result['debits']}")
print(f"Credits: {result['credits']}")
```

---

## Galileo API Integration

### Search Flights
```python
from flights.services.galileo_service import GalileoService
from datetime import datetime

galileo = GalileoService()

result = galileo.search_flights(
    origin='JED',
    destination='RUH',
    departure_date=datetime(2026, 3, 1).date(),
    adults=1,
    cabin_class='Y'
)
```

### Create Booking
```python
booking_result = galileo.create_booking(
    itinerary_data=selected_itinerary,
    passengers=passenger_list,
    agent=agent
)
```

### Issue Ticket (Triggers Automated Accounting!)
```python
ticket_result = galileo.issue_ticket(
    pnr=booking_result['pnr'],
    payment_info=payment_data
)
# ✓ Automated accounting triggered!
```

---

## Useful Queries

### Get All Transaction Logs
```python
from accounts.models.transaction_tracking import TransactionLog

logs = TransactionLog.objects.filter(agent=agent).order_by('-created_at')[:10]
for log in logs:
    print(f"{log.transaction_number}: {log.get_transaction_type_display()} - {log.total_amount}")
```

### Get Journal Entries
```python
from accounts.models.accounting import JournalEntry

entries = JournalEntry.objects.filter(user=agent).order_by('-created_at')[:10]
for entry in entries:
    print(f"{entry.account.code}: {entry.entry_type} {entry.amount}")
```

### Get Daily Summary
```python
from accounts.models.transaction_tracking import DailyTransactionSummary
from datetime import date

summary = DailyTransactionSummary.objects.get(
    agent=agent,
    summary_date=date.today()
)
print(f"Tickets Issued: {summary.tickets_issued}")
print(f"Total Sales: {summary.total_sales}")
```

---

## URLs

### Local Development
- Application: http://localhost:8000
- Admin: http://localhost:8000/admin
- API: http://localhost:8000/api

### Landing Page
- http://localhost:8000/accounts/landing/

---

## Environment Variables

### Required in `.env`:
```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@db:5432/mushqila

# Galileo GDS
GALILEO_PCC=YOUR_PCC
GALILEO_USERNAME=YOUR_USERNAME
GALILEO_PASSWORD=YOUR_PASSWORD
GALILEO_ENDPOINT=https://apac.universal-api.travelport.com/B2BGateway/connect/uAPI/AirService
```

---

## File Locations

### Models
- `accounts/models/transaction_tracking.py` - Transaction tracking
- `accounts/models/accounting.py` - Accounting models
- `flights/models/booking_models.py` - Booking, Ticket, Payment

### Services
- `accounts/services/agent_balance_service.py` - Balance tracking
- `accounts/services/automated_accounting_service.py` - Accounting automation
- `flights/services/galileo_service.py` - Galileo API integration

### Signals
- `accounts/signals/transaction_signals.py` - Automated signals

### Management Commands
- `accounts/management/commands/delete_demo_data.py` - Delete demo data
- `accounts/management/commands/initialize_accounts.py` - Initialize accounts

### Documentation
- `AUTOMATED-ACCOUNTING-SYSTEM.md` - Complete system docs
- `GALILEO-API-INTEGRATION-GUIDE.md` - Integration guide
- `DEMO-TEST-SUMMARY.md` - Demo test results
- `QUICK-REFERENCE.md` - This file

---

## Common Issues & Solutions

### Issue: Signals not firing
```bash
# Check signal registration
docker-compose exec web python manage.py shell
>>> import accounts.signals.transaction_signals
>>> # Should not raise any errors
```

### Issue: Migrations conflict
```bash
docker-compose exec web python manage.py migrate --fake accounts zero
docker-compose exec web python manage.py migrate accounts
```

### Issue: Static files not loading
```bash
docker-compose exec web python manage.py collectstatic --no-input
docker-compose restart web
```

---

## Git Commands

### Commit Changes
```bash
git add .
git commit -m "Your commit message"
```

### Push to GitHub
```bash
git push origin main
```

### Check Status
```bash
git status
```

---

## Production Deployment

### Build for Production
```bash
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Run Migrations in Production
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### Collect Static in Production
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input
```

---

**Last Updated**: ২৬ জানুয়ারি, ২০২৬
