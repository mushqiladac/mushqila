# Travelport Galileo GDS Integration Setup

## 📋 Prerequisites

আপনার Travelport থেকে এই credentials গুলো পেতে হবে:

1. **Username** - API access username
2. **Password** - API access password
3. **Branch Code** - Your branch/office code (e.g., P702214)
4. **Target Branch** - Target branch for transactions
5. **API Endpoint** - REST API URL (region based)

---

## 🔧 Step 1: Galileo Credentials পাওয়ার পর

### 1.1 Environment Variables Update করুন

**Local Development (.env):**
```bash
nano .env
```

যোগ করুন:
```bash
# Travelport Galileo GDS
TRAVELPORT_USERNAME=your_galileo_username
TRAVELPORT_PASSWORD=your_galileo_password
TRAVELPORT_BRANCH_CODE=P702214
TRAVELPORT_TARGET_BRANCH=P702214
TRAVELPORT_BASE_URL=https://americas-uapi.travelport.com
TRAVELPORT_REST_URL=https://americas-uapi.travelport.com/B2BGateway/connect/rest
```

**Production (.env.production on EC2):**
```bash
ssh -i your-key.pem ubuntu@16.170.104.186
cd /home/ubuntu/mushqila
nano .env.production
```

Update করুন:
```bash
TRAVELPORT_USERNAME=your_actual_username
TRAVELPORT_PASSWORD=your_actual_password
```

---

## 🧪 Step 2: API Connection Test করুন

### 2.1 Test Script চালান

```bash
# Local
python test_galileo.py

# Production (Docker)
docker-compose -f docker-compose.prod.yml exec web python test_galileo.py
```

### 2.2 Manual Test (Django Shell)

```bash
python manage.py shell
```

```python
from flights.services.galileo_client import galileo_client

# Test search
search_params = {
    'origin': 'DAC',
    'destination': 'DXB',
    'departure_date': '2026-03-15',
    'passengers': {'adult': 1},
    'cabin_class': 'Economy'
}

result = galileo_client.search_flights(search_params)
print(result)
```

---

## 📚 Step 3: Available Operations

### 3.1 Flight Search
```python
from flights.services.galileo_service import galileo_service

# Search flights
result = galileo_service.search_flights({
    'origin': 'DAC',
    'destination': 'DXB',
    'departure_date': '2026-03-15',
    'return_date': '2026-03-20',  # Optional
    'passengers': {'adult': 1, 'child': 0, 'infant': 0},
    'cabin_class': 'Economy'
})

if result['success']:
    flights = result['flights']
    print(f"Found {len(flights)} flights")
```

### 3.2 Create Booking
```python
booking_result = galileo_service.create_booking({
    'pricing_solution_key': 'xxx',  # From search results
    'passengers': [
        {
            'type': 'ADT',
            'title': 'Mr',
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1990-01-01',
            'gender': 'M',
            'passport_number': 'A12345678',
            'passport_expiry': '2030-12-31',
            'passport_country': 'BD'
        }
    ],
    'contact_info': {
        'email': 'john@example.com',
        'phone': '+8801712345678'
    },
    'user_id': 1
})

if booking_result['success']:
    pnr = booking_result['pnr']
    print(f"Booking created: {pnr}")
```

### 3.3 Issue Ticket
```python
ticket_result = galileo_service.issue_ticket({
    'booking_id': 123,
    'universal_record_locator': 'ABC123',
    'air_reservation_locator': 'XYZ789',
    'payment_info': {
        'type': 'Cash'
    }
})

if ticket_result['success']:
    print(f"Ticket issued: {ticket_result['ticket_numbers']}")
```

### 3.4 Void Ticket (within 24 hours)
```python
void_result = galileo_service.void_ticket({
    'ticket_number': '1234567890123',
    'universal_record_locator': 'ABC123',
    'booking_id': 123
})
```

### 3.5 Refund Ticket
```python
refund_result = galileo_service.refund_ticket({
    'ticket_number': '1234567890123',
    'universal_record_locator': 'ABC123',
    'booking_id': 123,
    'refund_type': 'Full'  # or 'Partial'
})
```

### 3.6 Reissue Ticket
```python
reissue_result = galileo_service.reissue_ticket({
    'ticket_number': '1234567890123',
    'universal_record_locator': 'ABC123',
    'booking_id': 123,
    'new_segments': [...],
    'additional_collection': 100.00
})
```

### 3.7 Cancel Booking
```python
cancel_result = galileo_service.cancel_booking({
    'pnr': 'ABC123',
    'booking_id': 123
})
```

### 3.8 Retrieve Booking
```python
booking_info = galileo_service.retrieve_booking('ABC123')
```

### 3.9 Get Fare Rules
```python
fare_rules = galileo_service.get_fare_rules({
    'fare_basis': 'YOWBD',
    'origin': 'DAC',
    'destination': 'DXB',
    'carrier': 'EK'
})
```

---

## 🔗 Step 4: Views এ Integration

### 4.1 Flight Search View Example

```python
# flights/views/search_views.py
from django.shortcuts import render
from flights.services.galileo_service import galileo_service

def search_flights(request):
    if request.method == 'POST':
        search_data = {
            'origin': request.POST.get('origin'),
            'destination': request.POST.get('destination'),
            'departure_date': request.POST.get('departure_date'),
            'return_date': request.POST.get('return_date'),
            'passengers': {
                'adult': int(request.POST.get('adults', 1)),
                'child': int(request.POST.get('children', 0)),
                'infant': int(request.POST.get('infants', 0))
            },
            'cabin_class': request.POST.get('cabin_class', 'Economy')
        }
        
        result = galileo_service.search_flights(search_data)
        
        if result['success']:
            return render(request, 'flights/search_results.html', {
                'flights': result['flights']
            })
        else:
            return render(request, 'flights/search.html', {
                'error': result['error']
            })
    
    return render(request, 'flights/search.html')
```

### 4.2 Booking View Example

```python
# flights/views/booking_views.py
from django.contrib.auth.decorators import login_required
from flights.services.galileo_service import galileo_service

@login_required
def create_booking(request):
    if request.method == 'POST':
        booking_data = {
            'pricing_solution_key': request.POST.get('solution_key'),
            'passengers': request.POST.get('passengers'),  # JSON data
            'contact_info': {
                'email': request.POST.get('email'),
                'phone': request.POST.get('phone')
            },
            'user_id': request.user.id
        }
        
        result = galileo_service.create_booking(booking_data)
        
        if result['success']:
            return redirect('booking_confirmation', booking_id=result['booking_id'])
        else:
            return render(request, 'flights/booking_error.html', {
                'error': result['error']
            })
    
    return render(request, 'flights/booking_form.html')
```

---

## 🚀 Step 5: Deploy করুন

### 5.1 Local Test করার পর

```bash
git add .
git commit -m "Add Galileo API credentials"
git push origin main
```

### 5.2 Production এ Update

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@16.170.104.186

# Update .env.production
cd /home/ubuntu/mushqila
nano .env.production

# Deploy
./deploy.sh
```

---

## 📊 API Endpoints Reference

### Galileo REST API Endpoints

```
Base URL: https://americas-uapi.travelport.com/B2BGateway/connect/rest

Search:
- POST /AirLowFareSearchReq - Low fare search
- POST /AirAvailabilitySearchReq - Availability search

Booking:
- POST /AirBookReq - Create booking
- POST /UniversalRecordRetrieveReq - Retrieve booking

Ticketing:
- POST /AirTicketReq - Issue ticket
- POST /AirVoidDocumentReq - Void ticket
- POST /AirRefundReq - Refund ticket
- POST /AirExchangeReq - Reissue/Exchange ticket

Cancellation:
- POST /AirCancelReq - Cancel booking

Fare Rules:
- POST /AirFareRulesReq - Get fare rules
```

---

## 🔍 Troubleshooting

### Issue: Authentication Failed
```bash
# Check credentials
echo $TRAVELPORT_USERNAME
echo $TRAVELPORT_PASSWORD

# Test connection
curl -u username:password https://americas-uapi.travelport.com/B2BGateway/connect/rest
```

### Issue: Invalid Branch Code
- Verify branch code with Travelport
- Ensure target branch matches your credentials

### Issue: API Timeout
- Check network connectivity
- Verify API endpoint URL
- Contact Travelport support

---

## 📞 Support

### Travelport Support
- **Technical Support**: https://support.travelport.com
- **Documentation**: https://developer.travelport.com
- **API Status**: https://status.travelport.com

### Mushqila Support
- **GitHub Issues**: https://github.com/mushqiladac/mushqila/issues
- **Email**: support@mushqila.com

---

## 📝 Notes

1. **Test Environment**: Travelport provides test credentials for development
2. **Rate Limits**: Check your API rate limits with Travelport
3. **Error Handling**: All methods return success/error status
4. **Logging**: All API calls are logged for debugging
5. **Transaction Safety**: Database operations use transactions

---

## ✅ Checklist

- [ ] Galileo credentials received from Travelport
- [ ] Environment variables updated (.env and .env.production)
- [ ] API connection tested successfully
- [ ] Flight search working
- [ ] Booking creation tested
- [ ] Ticket issuance tested
- [ ] All operations documented
- [ ] Error handling implemented
- [ ] Logging configured
- [ ] Production deployment completed

---

**Ready to go! 🚀**

Galileo API credentials পাওয়ার সাথে সাথে এই guide follow করুন এবং সব কিছু কাজ করবে!
