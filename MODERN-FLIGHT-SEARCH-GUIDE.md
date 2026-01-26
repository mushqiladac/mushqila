# Modern Flight Search Module - Integration Guide

## 📋 Overview

আপনার B2B Travel Platform এ একটি **modern, professional এবং GDS-ready** flight search module যোগ করা হয়েছে।

## ✨ Features

### 🎨 Modern UI/UX
- ✅ Gradient design with smooth animations
- ✅ Responsive layout (mobile, tablet, desktop)
- ✅ Interactive passenger selector
- ✅ Real-time form validation
- ✅ Loading states and feedback
- ✅ Professional color scheme

### 🛫 Flight Search Options
- ✅ One Way flights
- ✅ Round Trip flights
- ✅ Multi-City (up to 6 segments)
- ✅ Direct flights filter
- ✅ Flexible dates (±3 days)

### 👥 Passenger Management
- ✅ Adults (1-9)
- ✅ Children (0-9)
- ✅ Infants (0-adults count)
- ✅ Smart validation (infants ≤ adults)

### 💺 Cabin Classes
- ✅ Economy (Y)
- ✅ Premium Economy (W)
- ✅ Business (C)
- ✅ First Class (F)

### 🔌 Galileo GDS Integration Ready
- ✅ GDS field mapping
- ✅ API endpoint configuration
- ✅ Request/response handling
- ✅ Error management

---

## 🚀 Installation

### Step 1: Include the Component

Landing page এ modern search module যোগ করুন:

```html
<!-- accounts/templates/accounts/landing.html -->

{% load static %}

<!DOCTYPE html>
<html>
<head>
    <!-- Your existing head content -->
</head>
<body>
    <!-- Navbar -->
    
    <!-- Include Modern Flight Search -->
    {% include 'accounts/components/modern_flight_search.html' %}
    
    <!-- Rest of your content -->
</body>
</html>
```

### Step 2: Update URLs

`flights/urls.py` তে search endpoint যোগ করুন:

```python
from django.urls import path
from .views import search_views

urlpatterns = [
    # ... existing patterns
    
    # Flight Search API
    path('api/v1/api/search/', search_views.FlightSearchAPI.as_view(), name='flight_search_api'),
]
```

---

## 🔧 Galileo GDS Integration

### Configuration

`.env` file এ Galileo credentials যোগ করুন:

```env
# Galileo GDS Configuration
GALILEO_API_URL=https://api.travelport.com/v1
GALILEO_USERNAME=your_username
GALILEO_PASSWORD=your_password
GALILEO_TARGET_BRANCH=your_branch_code
GALILEO_PCC=your_pcc_code
```

### API Endpoint Setup

`flights/views/search_views.py` তে FlightSearchAPI update করুন:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from flights.services.galileo_service import GalileoService
import logging

logger = logging.getLogger(__name__)

class FlightSearchAPI(APIView):
    """
    Modern Flight Search API with Galileo GDS Integration
    """
    
    def post(self, request):
        try:
            # Get search parameters from request
            search_data = request.data
            
            # Validate required fields
            required_fields = ['origin', 'destination', 'departureDate', 'adults']
            for field in required_fields:
                if field not in search_data:
                    return Response({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }, status=400)
            
            # Initialize Galileo Service
            galileo = GalileoService()
            
            # Prepare search request based on trip type
            trip_type = search_data.get('tripType', 'one-way')
            
            if trip_type == 'multi-city':
                # Multi-city search
                segments = search_data.get('segments', [])
                result = galileo.search_multi_city_flights(
                    segments=segments,
                    passengers={
                        'adults': search_data.get('adults', 1),
                        'children': search_data.get('children', 0),
                        'infants': search_data.get('infants', 0)
                    },
                    cabin_class=search_data.get('cabinClass', 'Y'),
                    direct_only=search_data.get('directFlightsOnly', False)
                )
            else:
                # One-way or Round-trip search
                result = galileo.search_flights(
                    origin=search_data['origin'],
                    destination=search_data['destination'],
                    departure_date=search_data['departureDate'],
                    return_date=search_data.get('returnDate'),
                    passengers={
                        'adults': search_data.get('adults', 1),
                        'children': search_data.get('children', 0),
                        'infants': search_data.get('infants', 0)
                    },
                    cabin_class=search_data.get('cabinClass', 'Y'),
                    direct_only=search_data.get('directFlightsOnly', False),
                    flexible_dates=search_data.get('flexibleDates', False)
                )
            
            if result['success']:
                # Save search to database
                from flights.models import FlightSearch
                search = FlightSearch.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    origin=search_data['origin'],
                    destination=search_data['destination'],
                    departure_date=search_data['departureDate'],
                    return_date=search_data.get('returnDate'),
                    adults=search_data.get('adults', 1),
                    children=search_data.get('children', 0),
                    infants=search_data.get('infants', 0),
                    cabin_class=search_data.get('cabinClass', 'Y'),
                    trip_type=trip_type,
                    search_results=result['flights']
                )
                
                return Response({
                    'success': True,
                    'search_id': str(search.id),
                    'flights_count': len(result['flights']),
                    'message': 'Flights found successfully'
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'No flights found')
                }, status=404)
                
        except Exception as e:
            logger.error(f"Flight search error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'An error occurred while searching flights'
            }, status=500)
```

### Galileo Service Methods

`flights/services/galileo_service.py` তে নিচের methods আছে:

```python
class GalileoService:
    def search_flights(self, origin, destination, departure_date, 
                      return_date=None, passengers=None, cabin_class='Y',
                      direct_only=False, flexible_dates=False):
        """
        Search flights using Galileo GDS
        
        Args:
            origin (str): Origin airport code (e.g., 'JED')
            destination (str): Destination airport code (e.g., 'DAC')
            departure_date (str): Departure date (YYYY-MM-DD)
            return_date (str, optional): Return date for round-trip
            passengers (dict): {'adults': 1, 'children': 0, 'infants': 0}
            cabin_class (str): Y/W/C/F (Economy/Premium/Business/First)
            direct_only (bool): Search only direct flights
            flexible_dates (bool): Search ±3 days
        
        Returns:
            dict: {'success': bool, 'flights': list, 'error': str}
        """
        # Implementation in galileo_service.py
        pass
    
    def search_multi_city_flights(self, segments, passengers, 
                                  cabin_class='Y', direct_only=False):
        """
        Search multi-city flights
        
        Args:
            segments (list): [{'origin': 'JED', 'destination': 'DAC', 'date': '2025-02-01'}, ...]
            passengers (dict): {'adults': 1, 'children': 0, 'infants': 0}
            cabin_class (str): Y/W/C/F
            direct_only (bool): Search only direct flights
        
        Returns:
            dict: {'success': bool, 'flights': list, 'error': str}
        """
        # Implementation in galileo_service.py
        pass
```

---

## 📊 Data Flow

```
User Input (Modern UI)
    ↓
JavaScript Form Handler
    ↓
AJAX POST Request
    ↓
Django View (FlightSearchAPI)
    ↓
Galileo Service
    ↓
Galileo GDS API
    ↓
Response Processing
    ↓
Save to Database
    ↓
Redirect to Results Page
```

---

## 🎨 Customization

### Colors

CSS variables customize করুন:

```css
:root {
    --primary-gradient-start: #667eea;  /* Purple */
    --primary-gradient-end: #764ba2;    /* Dark Purple */
    --success-color: #10b981;           /* Green */
    --danger-color: #dc2626;            /* Red */
}
```

### GDS Endpoint

Form এর `data-gds-endpoint` attribute change করুন:

```html
<form id="flight-search-form" data-gds-endpoint="/your/custom/endpoint/">
```

### Airport List

JavaScript এ airport list update করুন:

```javascript
const airports = [
    { code: 'JED', name: 'Jeddah', country: 'Saudi Arabia' },
    { code: 'RUH', name: 'Riyadh', country: 'Saudi Arabia' },
    // Add more airports...
];
```

---

## 🧪 Testing

### Local Testing

```bash
# Start Docker containers
docker-compose up -d

# Access the page
http://localhost:8000/accounts/landing/
```

### Test Search

1. Select trip type (One Way/Round Trip/Multi City)
2. Enter origin and destination
3. Select dates
4. Choose passengers and class
5. Click "Search Flights"
6. Check browser console for API calls
7. Verify response in Network tab

---

## 🔍 Troubleshooting

### Issue: Search button not working

**Solution:**
- Check browser console for JavaScript errors
- Verify CSRF token is present
- Check API endpoint URL

### Issue: No flights found

**Solution:**
- Verify Galileo credentials in `.env`
- Check Galileo service logs
- Ensure airport codes are valid IATA codes

### Issue: Styling issues

**Solution:**
- Clear browser cache
- Check if Flatpickr CSS is loaded
- Verify Bootstrap 5 is included

---

## 📱 Mobile Responsiveness

Module টি সব device এ responsive:

- **Mobile (< 768px)**: Single column layout
- **Tablet (768px - 1024px)**: 2 column layout
- **Desktop (> 1024px)**: Full 4 column layout

---

## 🌐 Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

---

## 📚 Additional Resources

- [Galileo GDS Documentation](GALILEO-SETUP.md)
- [API Integration Guide](DEPLOYMENT.md)
- [Quick Commands](QUICK-COMMANDS.md)

---

## 🎯 Next Steps

1. ✅ Modern search module installed
2. ⏳ Configure Galileo GDS credentials
3. ⏳ Test search functionality
4. ⏳ Customize colors and branding
5. ⏳ Add airport autocomplete API
6. ⏳ Implement results page
7. ⏳ Add booking flow

---

## 💡 Tips

### Performance
- Cache airport list in localStorage
- Implement debounce for autocomplete
- Use lazy loading for images

### UX Improvements
- Add loading skeleton
- Show recent searches
- Add popular routes
- Implement fare calendar

### Security
- Validate all inputs server-side
- Sanitize user data
- Rate limit API calls
- Use HTTPS only

---

## 📞 Support

যদি কোন সমস্যা হয়:

1. Check logs: `docker-compose logs web`
2. Review browser console
3. Check Network tab for API calls
4. Verify Galileo credentials

---

**Created:** January 26, 2026
**Status:** ✅ Ready for Integration
**Galileo GDS:** ✅ Integration Ready
