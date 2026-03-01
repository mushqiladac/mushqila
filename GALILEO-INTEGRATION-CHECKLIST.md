# Galileo Integration Checklist ✅

**Use this checklist to track your Galileo GDS integration progress**

---

## Phase 1: Prerequisites ⏳

### Get Galileo Credentials
- [ ] Contact Travelport sales/support
- [ ] Request API access
- [ ] Receive PCC (Pseudo City Code)
- [ ] Receive API username
- [ ] Receive API password
- [ ] Receive target branch code
- [ ] Get test environment access
- [ ] Get production environment access

### Install Required Packages
- [ ] Install zeep: `pip install zeep`
- [ ] Install requests: `pip install requests`
- [ ] Install lxml: `pip install lxml`
- [ ] Verify installations: `pip list | grep -E "zeep|requests|lxml"`

### Update Environment Variables
- [ ] Open `.env` file
- [ ] Add `GALILEO_PCC=YOUR_PCC`
- [ ] Add `GALILEO_USERNAME=YOUR_USERNAME`
- [ ] Add `GALILEO_PASSWORD=YOUR_PASSWORD`
- [ ] Add `GALILEO_TARGET_BRANCH=YOUR_BRANCH`
- [ ] Add `GALILEO_PROVIDER_CODE=1G`
- [ ] Add test endpoint URLs
- [ ] Save and restart server

---

## Phase 2: Connection Testing ⏳

### Test Basic Connection
- [ ] Open Django shell: `python manage.py shell`
- [ ] Import adapter: `from flights.services.gds_adapter import get_gds_adapter`
- [ ] Get Galileo adapter: `gds = get_gds_adapter('galileo')`
- [ ] Verify client initialized: Check for no errors
- [ ] Test credentials: Try a simple API call

### Test Flight Search
- [ ] Prepare search parameters
- [ ] Call `gds.search_flights({...})`
- [ ] Verify response success
- [ ] Check flight results returned
- [ ] Verify pricing information
- [ ] Check airline codes
- [ ] Verify departure/arrival times

### Test Fare Rules
- [ ] Select a flight from search results
- [ ] Call `gds.get_fare_rules({...})`
- [ ] Verify fare rules returned
- [ ] Check cancellation policy
- [ ] Check change policy
- [ ] Verify baggage allowance

---

## Phase 3: Booking Testing ⏳

### Test Booking Creation
- [ ] Prepare passenger data
- [ ] Prepare contact information
- [ ] Call `gds.create_booking({...})`
- [ ] Verify PNR created
- [ ] Check booking reference
- [ ] Verify passenger names
- [ ] Check flight segments
- [ ] Verify pricing

### Test Booking Retrieval
- [ ] Use PNR from previous test
- [ ] Call `gds.retrieve_booking('PNR')`
- [ ] Verify booking details
- [ ] Check passenger information
- [ ] Verify flight segments
- [ ] Check booking status

### Test Booking Modification
- [ ] Retrieve existing booking
- [ ] Prepare modification data
- [ ] Call `gds.modify_booking('PNR', {...})`
- [ ] Verify changes applied
- [ ] Check updated pricing

---

## Phase 4: Ticketing Testing ⏳

### Test Ticket Issuance
- [ ] Create test booking
- [ ] Prepare payment information
- [ ] Call `gds.issue_ticket({...})`
- [ ] Verify ticket numbers returned
- [ ] Check ticket status in database
- [ ] **IMPORTANT**: Verify automated accounting triggered
- [ ] Check TransactionLog created
- [ ] Verify JournalEntry posted
- [ ] Check agent balance updated
- [ ] Verify daily summary updated

### Verify Automated Accounting
- [ ] Check transaction log: `TransactionLog.objects.latest()`
- [ ] Verify accounting_posted = True
- [ ] Check journal entries: `JournalEntry.objects.filter(...)`
- [ ] Verify debits = credits (balanced)
- [ ] Check agent ledger updated
- [ ] Verify daily summary correct
- [ ] Check audit log created

### Test Ticket Void
- [ ] Issue a test ticket
- [ ] Call `gds.void_ticket('TICKET_NUMBER')`
- [ ] Verify void successful
- [ ] Check ticket status = 'voided'
- [ ] **IMPORTANT**: Verify reversal accounting triggered
- [ ] Check reversal journal entries
- [ ] Verify agent balance adjusted

### Test Ticket Refund
- [ ] Issue a test ticket
- [ ] Call `gds.refund_ticket({...})`
- [ ] Verify refund processed
- [ ] Check refund amount
- [ ] Check penalty amount
- [ ] Verify ticket status = 'refunded'
- [ ] **IMPORTANT**: Verify refund accounting triggered
- [ ] Check refund journal entries

---

## Phase 5: Advanced Features ⏳

### Test Seat Map
- [ ] Get flight segment
- [ ] Call `gds.get_seat_map({...})`
- [ ] Verify seat map returned
- [ ] Check available seats
- [ ] Verify seat pricing

### Test Ancillary Services
- [ ] Create booking
- [ ] Prepare ancillary services (baggage, meals)
- [ ] Call `gds.add_ancillary_services('PNR', [...])`
- [ ] Verify services added
- [ ] Check updated pricing

### Test Queue Management
- [ ] Create booking
- [ ] Call `gds.queue_place('PNR', 'QUEUE_NUMBER')`
- [ ] Verify PNR in queue
- [ ] Call `gds.queue_retrieve('QUEUE_NUMBER')`
- [ ] Verify PNR retrieved

---

## Phase 6: Error Handling ⏳

### Test Error Scenarios
- [ ] Test with invalid credentials
- [ ] Test with invalid PCC
- [ ] Test with invalid airport codes
- [ ] Test with invalid dates
- [ ] Test with invalid passenger data
- [ ] Test with insufficient balance
- [ ] Test with expired session
- [ ] Verify error messages clear
- [ ] Check error logging works

### Test Timeout Handling
- [ ] Test with slow connection
- [ ] Verify timeout settings work
- [ ] Check retry logic
- [ ] Verify graceful degradation

---

## Phase 7: Integration Testing ⏳

### End-to-End Workflow
- [ ] Search flights
- [ ] Select flight
- [ ] Create booking
- [ ] Add passengers
- [ ] Issue ticket
- [ ] Verify automated accounting
- [ ] Check customer notification
- [ ] Verify agent balance
- [ ] Generate invoice
- [ ] Complete workflow

### B2C Integration
- [ ] Customer searches flights
- [ ] Customer books flight
- [ ] Customer pays
- [ ] Ticket issued automatically
- [ ] Customer earns loyalty points
- [ ] Customer receives confirmation
- [ ] Customer can view booking
- [ ] Customer can manage booking

### Accounting Verification
- [ ] Issue 10 test tickets
- [ ] Verify all accounting posted
- [ ] Check all balances correct
- [ ] Verify daily summary accurate
- [ ] Generate financial reports
- [ ] Verify reports accurate

---

## Phase 8: Performance Testing ⏳

### Load Testing
- [ ] Test 10 concurrent searches
- [ ] Test 5 concurrent bookings
- [ ] Test 3 concurrent ticketing
- [ ] Measure response times
- [ ] Check for errors
- [ ] Verify system stability

### Optimization
- [ ] Enable caching where appropriate
- [ ] Optimize database queries
- [ ] Add indexes if needed
- [ ] Monitor memory usage
- [ ] Check for bottlenecks

---

## Phase 9: Production Preparation ⏳

### Switch to Production
- [ ] Update .env with production endpoints
- [ ] Update credentials to production
- [ ] Test production connection
- [ ] Verify production access
- [ ] Test production search
- [ ] Test production booking

### Monitoring Setup
- [ ] Enable Django logging
- [ ] Setup error alerts
- [ ] Configure email notifications
- [ ] Setup performance monitoring
- [ ] Enable transaction tracking
- [ ] Configure backup systems

### Documentation
- [ ] Document API credentials location
- [ ] Document error handling procedures
- [ ] Create troubleshooting guide
- [ ] Document common issues
- [ ] Create staff training materials
- [ ] Document escalation procedures

---

## Phase 10: Staff Training ⏳

### Train Staff
- [ ] Explain GDS integration
- [ ] Show how to search flights
- [ ] Demonstrate booking process
- [ ] Explain ticketing workflow
- [ ] Show automated accounting
- [ ] Explain error handling
- [ ] Practice void/refund procedures
- [ ] Review reporting features

### Create Procedures
- [ ] Document daily procedures
- [ ] Create checklists
- [ ] Define approval workflows
- [ ] Document exception handling
- [ ] Create escalation matrix

---

## Phase 11: Go Live ⏳

### Pre-Launch
- [ ] Final system check
- [ ] Verify all tests passed
- [ ] Check production credentials
- [ ] Verify monitoring active
- [ ] Confirm staff trained
- [ ] Review emergency procedures
- [ ] Backup current system
- [ ] Prepare rollback plan

### Launch
- [ ] Enable production access
- [ ] Monitor first transactions
- [ ] Verify automated accounting
- [ ] Check for errors
- [ ] Monitor performance
- [ ] Verify customer notifications
- [ ] Check agent balances
- [ ] Verify reports accurate

### Post-Launch
- [ ] Monitor for 24 hours
- [ ] Review error logs
- [ ] Check transaction volumes
- [ ] Verify accounting accuracy
- [ ] Gather staff feedback
- [ ] Document issues
- [ ] Plan improvements

---

## Phase 12: Optimization ⏳

### Performance Optimization
- [ ] Analyze response times
- [ ] Identify bottlenecks
- [ ] Implement caching
- [ ] Optimize queries
- [ ] Add indexes
- [ ] Review architecture

### Feature Enhancement
- [ ] Gather user feedback
- [ ] Identify pain points
- [ ] Plan new features
- [ ] Implement improvements
- [ ] Test enhancements
- [ ] Deploy updates

---

## Quick Reference

### Essential Commands

```bash
# Test connection
python manage.py shell
>>> from flights.services.gds_adapter import get_gds_adapter
>>> gds = get_gds_adapter('galileo')
>>> result = gds.search_flights({...})

# Check accounting
python manage.py shell
>>> from accounts.models.transaction_tracking import TransactionLog
>>> TransactionLog.objects.latest('created_at')

# Verify balance
python manage.py shell
>>> from accounts.services.agent_balance_service import AgentBalanceService
>>> service = AgentBalanceService()
>>> balance = service.get_agent_balance(agent)
```

### Important Files

- `.env` - Credentials
- `flights/services/gds_adapter.py` - GDS interface
- `flights/services/galileo_client.py` - SOAP client
- `accounts/services/automated_accounting_service.py` - Accounting
- `GALILEO-INTEGRATION-READY.md` - Complete guide

---

## Progress Tracking

**Total Tasks**: 150+
**Completed**: ___
**In Progress**: ___
**Remaining**: ___

**Estimated Time**: 2-3 days
**Actual Time**: ___

---

## Notes

Use this space to track issues, decisions, and important information:

```
Date: ___________
Issue: ___________
Resolution: ___________

Date: ___________
Issue: ___________
Resolution: ___________
```

---

**Good luck with your Galileo integration!** 🚀
