# Functional Search Widget Implementation Guide

## ✅ Completed Steps:

1. ✅ Created `flights/models.py` - Airport & FlightSearch models
2. ✅ Created `flights/management/commands/load_airports.py` - Sample airport data
3. ✅ Created `flights/views.py` - API endpoints for airport search & flight search
4. ✅ Created `flights/urls.py` - URL routing
5. ✅ Updated `config/urls.py` - Added flights URLs

## 🔄 Next Steps to Complete:

### Step 6: Run Migrations
```bash
python manage.py makemigrations flights
python manage.py migrate
python manage.py load_airports
```

### Step 7: Update modern_search_widget.html
Add functional JavaScript with:
- Flatpickr date picker
- Airport autocomplete
- Passenger/class selector
- Form validation
- AJAX submission

### Step 8: Add CDN Links to landing.html
```html
<!-- In <head> section -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
<script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
```

### Step 9: Create Passenger Selector Modal
Add modal for selecting passengers and cabin class

### Step 10: Galileo GDS Integration
Update `flights/services/galileo_service.py` to integrate with Travelport Galileo GDS API

## Files Created:
- `flights/models.py`
- `flights/views.py`
- `flights/urls.py`
- `flights/management/commands/load_airports.py`

## Files Updated:
- `config/urls.py`

## Next Session Tasks:
1. Complete frontend JavaScript implementation
2. Add date picker
3. Add autocomplete
4. Add passenger selector
5. Test the complete flow
6. Integrate Galileo GDS API

## Demo Features:
- ✅ Airport search with autocomplete
- ✅ Date picker for journey dates
- ✅ Passenger & class selection
- ✅ Form validation
- ✅ Demo flight results
- 🔄 Galileo GDS integration (pending)
