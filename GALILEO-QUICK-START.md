# Galileo GDS - Quick Start Guide

**5 মিনিটে Galileo API Integration শুরু করুন!**

---

## 🚀 Step 1: Install Packages (1 minute)

```bash
pip install zeep requests lxml
```

---

## 🔑 Step 2: Add Credentials (2 minutes)

`.env` file এ add করুন:

```bash
# Galileo Credentials (Get from Travelport)
GALILEO_PCC=YOUR_PCC
GALILEO_USERNAME=YOUR_USERNAME
GALILEO_PASSWORD=YOUR_PASSWORD
GALILEO_TARGET_BRANCH=YOUR_BRANCH
GALILEO_PROVIDER_CODE=1G
```

---

## ✅ Step 3: Test Connection (1 minute)

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

print(f"Success: {result['success']}")
print(f"Flights found: {result.get('count', 0)}")
```

---

## 🎫 Step 4: Issue Your First Ticket (1 minute)

```python
# After creating booking...
ticket_result = gds.issue_ticket({
    'pnr': 'ABC123',
    'air_reservation_locator': 'XYZ789',
    'payment_info': {
        'type': 'Cash'
    }
})

if ticket_result['success']:
    print("✅ Ticket issued!")
    print("🎯 Automated accounting done!")
```

---

## 🎉 Done!

আপনার Galileo integration এখন কাজ করছে এবং automated accounting চালু আছে!

### Next Steps:

1. Read full guide: `GALILEO-INTEGRATION-READY.md`
2. Check automated accounting: `AUTOMATED-ACCOUNTING-SYSTEM.md`
3. Explore B2C features: `B2C-READY-STATUS.md`

---

## 📞 Need Help?

- Check `GALILEO-INTEGRATION-READY.md` for detailed documentation
- Review `TROUBLESHOOTING.md` for common issues
- Contact Travelport support for API issues
