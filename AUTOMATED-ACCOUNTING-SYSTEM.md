# Automated Transaction Tracking & Accounting System

## Overview

Complete real-time automated accounting system for B2B travel platform. All ticketing operations (issue, void, cancel, refund) automatically update:
- Central accounting system (double-entry bookkeeping)
- Agent balances
- Outstanding amounts
- Transaction logs
- Daily/Monthly reports

## System Architecture

### 1. Transaction Tracking Models

**TransactionLog** - Central log for all operations
- Tracks: Issue, Void, Cancel, Refund, Reissue, Payments, Commissions
- Auto-generates unique transaction numbers
- Links to booking and agent
- Stores financial details (base, tax, fees, commission)
- Tracks accounting posting status

**AgentLedger** - Agent-wise financial ledger
- Running balance for each agent
- Debit/Credit entries
- Links to transaction log

**DailyTransactionSummary** - Daily statistics per agent
- Transaction counts (issued, voided, cancelled, refunded)
- Financial totals (sales, refunds, commissions)
- Opening/closing balance

**MonthlyAgentReport** - Monthly consolidated reports
- Complete monthly statistics
- Commission details
- Detailed breakdown in JSON

**TransactionAuditLog** - Immutable audit trail
- Tracks all changes
- Before/after state
- IP address and user agent for security

### 2. Automated Signals

All signals are in `accounts/signals/transaction_signals.py`:

**handle_ticket_issue** - Triggers on Ticket.status = 'issued'
- Creates TransactionLog
- Posts to accounting (double-entry)
- Updates agent ledger
- Updates daily summary

**handle_ticket_void** - Triggers on Ticket.status = 'voided'
- Creates void transaction
- Reverses original issue
- Posts reversal entries
- Updates balances

**handle_ticket_refund** - Triggers on Ticket.status = 'refunded'
- Creates refund transaction
- Calculates penalties
- Posts refund entries
- Updates balances

**handle_payment_received** - Triggers on Payment.status = 'captured'/'authorized'
- Creates payment transaction
- Posts to accounting
- Updates agent balance

**handle_commission_transaction** - Triggers on CommissionTransaction creation
- Creates commission transaction
- Posts to accounting
- Updates balances

**update_agent_ledger** - Auto-updates ledger on every transaction
- Calculates running balance
- Creates ledger entry

**update_daily_summary** - Auto-updates daily statistics
- Increments counters
- Updates totals

**create_audit_log** - Creates audit trail for every change
- Immutable log
- Tracks who, when, what

### 3. Automated Accounting Service

**AutomatedAccountingService** (`accounts/services/automated_accounting_service.py`)

Implements double-entry bookkeeping:

**Ticket Issue:**
```
Debit:  Accounts Receivable (1200)  [Total Amount]
Credit: Ticket Revenue (4001)       [Base Amount]
Credit: Tax Payable (2100)          [Tax Amount]
```

**Ticket Void:**
```
Debit:  Ticket Revenue (4001)       [Base Amount]
Debit:  Tax Payable (2100)          [Tax Amount]
Credit: Accounts Receivable (1200)  [Total Amount]
```

**Ticket Refund:**
```
Debit:  Ticket Revenue (4001)       [Refund Amount]
Debit:  Refund Expenses (5003)      [Penalty]
Credit: Cash (1001)                 [Net Refund]
```

**Payment Received:**
```
Debit:  Cash (1001)                 [Amount]
Debit:  Payment Fees (5002)         [Fees]
Credit: Accounts Receivable (1200)  [Total]
```

**Commission Earned:**
```
Debit:  Commissions Paid (5004)     [Amount]
Credit: Commission Payable (2200)   [Amount]
```

**Commission Paid:**
```
Debit:  Commission Payable (2200)   [Amount]
Credit: Cash (1001)                 [Amount]
```

### 4. Agent Balance Service

**AgentBalanceService** (`accounts/services/agent_balance_service.py`)

**get_agent_balance(agent)** - Real-time balance
Returns:
- Current balance
- Outstanding amount
- Credit limit
- Available credit
- Total sales/payments/refunds
- Last payment/transaction date

**get_outstanding_details(agent)** - Detailed breakdown
Returns:
- List of unpaid tickets
- Aging analysis (0-7, 8-30, 31-60, 61-90, 90+ days)
- Days outstanding per ticket

**get_payment_history(agent, days=30)** - Payment history
Returns:
- List of payments
- Total paid in period

**check_credit_limit(agent, amount)** - Credit check
Returns:
- Allowed/not allowed
- Available credit
- Shortfall if any

**get_all_agents_balances()** - All agents summary (for staff)
Returns:
- Balance for all agents
- Total outstanding
- Credit utilization

**record_payment(agent, amount, method, reference)** - Record payment
- Creates payment transaction
- Auto-updates via signals

**get_credit_utilization_report()** - Credit utilization
Returns:
- Agents by utilization category (healthy, moderate, high, critical)

### 5. Automated Reporting Service

**AutomatedReportingService** (`accounts/services/automated_reporting_service.py`)

**generate_agent_daily_report(agent, date)** - Daily report
**generate_agent_monthly_report(agent, year, month)** - Monthly report
**generate_all_agents_summary(date)** - All agents summary
**generate_financial_statement(start_date, end_date)** - Financial statements

## Setup Instructions

### 1. Create Migrations

```bash
# In Docker
docker-compose exec web python manage.py makemigrations accounts

# Or locally
python manage.py makemigrations accounts
```

### 2. Run Migrations

```bash
# In Docker
docker-compose exec web python manage.py migrate

# Or locally
python manage.py migrate
```

### 3. Initialize Chart of Accounts

```bash
# In Docker
docker-compose exec web python manage.py initialize_accounts

# Or locally
python manage.py initialize_accounts
```

This creates:
- 1001: Cash and Cash Equivalents
- 1200: Accounts Receivable
- 2100: Tax Payable
- 2200: Commission Payable
- 4001: Ticket Revenue
- 4002: Ancillary Revenue
- 5002: Payment Processing Fees
- 5003: Refund Processing Expenses
- 5004: Commissions Paid

### 4. Add Credit Limit to User Model (if not exists)

Add these fields to User model in `accounts/models/core.py`:

```python
credit_limit = models.DecimalField(
    _('Credit Limit'), 
    max_digits=12, 
    decimal_places=2, 
    default=Decimal('0.00')
)

agent_code = models.CharField(
    _('Agent Code'), 
    max_length=20, 
    blank=True
)
```

Then create migration:
```bash
python manage.py makemigrations accounts
python manage.py migrate
```

## Usage Examples

### Check Agent Balance

```python
from accounts.services.agent_balance_service import AgentBalanceService

service = AgentBalanceService()
balance_info = service.get_agent_balance(agent)

print(f"Current Balance: {balance_info['current_balance']}")
print(f"Outstanding: {balance_info['outstanding_amount']}")
print(f"Available Credit: {balance_info['available_credit']}")
```

### Get Outstanding Details

```python
outstanding = service.get_outstanding_details(agent)

print(f"Total Outstanding: {outstanding['total_outstanding']}")
print(f"Outstanding Count: {outstanding['outstanding_count']}")

# Aging analysis
for category, amount in outstanding['aging_summary'].items():
    print(f"{category}: {amount}")
```

### Check Credit Before Booking

```python
requested_amount = Decimal('5000.00')
check = service.check_credit_limit(agent, requested_amount)

if check['allowed']:
    print(f"Credit approved. Remaining: {check['remaining_credit']}")
else:
    print(f"Insufficient credit. Shortfall: {check['shortfall']}")
```

### Record Payment

```python
result = service.record_payment(
    agent=agent,
    amount=Decimal('10000.00'),
    payment_method='bank_transfer',
    reference='TRF20260126001',
    notes='Payment for January bookings'
)

if result['success']:
    print(f"Payment recorded: {result['transaction_number']}")
```

### Get All Agents Balances (Staff)

```python
summary = service.get_all_agents_balances()

print(f"Total Agents: {summary['total_agents']}")
print(f"Total Outstanding: {summary['total_outstanding']}")

for agent_info in summary['agents']:
    print(f"{agent_info['agent_name']}: {agent_info['outstanding_amount']}")
```

### Generate Reports

```python
from accounts.services.automated_reporting_service import AutomatedReportingService
from datetime import date

reporting = AutomatedReportingService()

# Daily report
daily = reporting.generate_agent_daily_report(agent, date.today())

# Monthly report
monthly = reporting.generate_agent_monthly_report(agent, 2026, 1)

# All agents summary
summary = reporting.generate_all_agents_summary(date.today())
```

## Real-Time Updates

Everything updates automatically when:

1. **Ticket Issued** → Transaction log created → Accounting posted → Balance updated → Daily summary updated
2. **Ticket Voided** → Void transaction created → Original reversed → Balance adjusted
3. **Ticket Refunded** → Refund transaction created → Accounting posted → Balance updated
4. **Payment Received** → Payment transaction created → Balance updated → Outstanding reduced
5. **Commission Earned** → Commission transaction created → Accounting posted

## API Endpoints (To Be Created)

Recommended endpoints for views:

```python
# Agent Balance Dashboard
GET /api/agent/balance/
GET /api/agent/outstanding/
GET /api/agent/payment-history/
POST /api/agent/record-payment/

# Staff Reports
GET /api/staff/all-agents-balances/
GET /api/staff/credit-utilization/
GET /api/staff/daily-report/
GET /api/staff/monthly-report/

# Transaction Logs
GET /api/transactions/
GET /api/transactions/<id>/
GET /api/transactions/audit-trail/
```

## Database Indexes

All models have proper indexes for performance:
- Transaction logs: agent + date, type + status, booking + type
- Agent ledger: agent + date, agent + type
- Daily summary: agent + date, date
- Monthly report: agent + year + month

## Security & Compliance

- **Audit Trail**: Every transaction change logged with IP and user agent
- **Immutable Logs**: TransactionAuditLog cannot be modified
- **Double-Entry Verification**: Built-in verification method
- **Credit Limit Enforcement**: Automatic credit checks
- **Real-time Balance**: Always up-to-date, no batch processing

## Testing Checklist

1. ✓ Create migrations
2. ✓ Run migrations
3. ✓ Initialize chart of accounts
4. ✓ Issue a ticket → Check transaction log → Verify accounting entries → Check balance
5. ✓ Void a ticket → Verify reversal → Check balance update
6. ✓ Refund a ticket → Verify accounting → Check balance
7. ✓ Record payment → Verify ledger update → Check balance
8. ✓ Check outstanding details → Verify aging analysis
9. ✓ Generate daily report → Verify statistics
10. ✓ Generate monthly report → Verify totals

## Troubleshooting

### Signals not firing?
- Check `accounts/apps.py` has signal imports
- Check `accounts/__init__.py` has app config
- Restart Django server

### Accounting entries not balanced?
```python
from accounts.services.automated_accounting_service import AutomatedAccountingService

service = AutomatedAccountingService()
result = service.verify_double_entry('TI-20260126120000-abc123')
print(result)  # Shows debits, credits, difference
```

### Balance not updating?
- Check if signals are registered
- Check transaction log status is 'completed'
- Check agent ledger entries

## Next Steps

1. Create views for agent balance dashboard
2. Create views for staff reports
3. Create API endpoints
4. Add credit limit field to User model
5. Create frontend components for balance display
6. Add email notifications for low credit
7. Add SMS alerts for critical credit utilization
8. Create Excel export for reports
9. Add PDF generation for statements
10. Implement automated monthly report generation (Celery task)

## Files Modified/Created

### Created:
- `accounts/models/transaction_tracking.py` - Transaction tracking models
- `accounts/signals/transaction_signals.py` - Automated signals
- `accounts/services/automated_accounting_service.py` - Accounting automation
- `accounts/services/automated_reporting_service.py` - Reporting service
- `accounts/services/agent_balance_service.py` - Balance tracking
- `accounts/management/commands/initialize_accounts.py` - Setup command

### Modified:
- `accounts/models/__init__.py` - Added transaction tracking imports
- `accounts/apps.py` - Registered signals
- `accounts/__init__.py` - App config

### Existing (Used):
- `accounts/models/accounting.py` - Base accounting models
- `flights/models/booking_models.py` - Ticket, Payment, Booking models

## Support

For issues or questions:
1. Check signal registration in `accounts/apps.py`
2. Check transaction log status
3. Verify chart of accounts exists
4. Check Django logs for errors
5. Use `verify_double_entry()` to check accounting balance

---

**Status**: Ready for testing
**Version**: 1.0
**Date**: January 26, 2026
