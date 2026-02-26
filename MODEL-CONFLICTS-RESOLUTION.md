# Model Conflicts Between Accounts and Flights Apps

## Identified Conflicts

### 1. Payment Model
- **Location 1**: `accounts/models/financial.py` (Line 14)
- **Location 2**: `flights/models/booking_models.py` (Line 528)
- **Issue**: Both apps define a `Payment` model, which will cause conflicts in Django's model registry

### 2. Refund Model
- **Location 1**: `accounts/models/financial.py` (Line 175)
- **Location 2**: `flights/models/booking_models.py` (Line 617)
- **Issue**: Both apps define a `Refund` model, which will cause conflicts in Django's model registry

## Resolution Strategy

### Option 1: Use App Labels (Recommended)
Keep both models but always reference them with app labels:
```python
# In accounts app
from accounts.models import Payment as AccountsPayment
from accounts.models import Refund as AccountsRefund

# In flights app
from flights.models import Payment as FlightsPayment
from flights.models import Refund as FlightsRefund
```

### Option 2: Rename Models
Rename one set of models to be more specific:
- `accounts.Payment` → Keep as is (general payment)
- `flights.Payment` → Rename to `FlightPayment`
- `accounts.Refund` → Keep as is (general refund)
- `flights.Refund` → Rename to `FlightRefund`

### Option 3: Consolidate Models
Use only the accounts app models for payments and refunds, and create ForeignKey relationships from flights app.

## Current Status

### Fixed Issues
✅ Fixed `airport_search` view to use `iata_code` instead of `code`
✅ Fixed `flight_search` view to handle ForeignKey relationships for origin/destination
✅ Added proper Airport object lookup by IATA code
✅ Added search_hash generation for FlightSearch
✅ Made FlightSearch creation conditional on user authentication

### Remaining Issues
⚠️ Model name conflicts (Payment, Refund) - Currently not causing errors but may cause issues later
⚠️ Need to run migrations for flights app
⚠️ Need to load airport data

## Next Steps

1. **Test the current setup**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Load airport data**:
   ```bash
   python manage.py load_airports
   ```

3. **Decide on conflict resolution**:
   - If no issues arise, keep current structure with app labels
   - If conflicts occur, implement Option 2 (rename flights models)

4. **Update JavaScript**:
   - Ensure `search_type` is sent instead of `trip_type`
   - Ensure airport codes match IATA format

## Model Field Mapping

### Airport Model
- Primary Key: `iata_code` (CharField, max_length=3)
- Fields: `icao_code`, `name`, `city`, `country`, `country_code`, `timezone`, `latitude`, `longitude`
- Search fields: `iata_code`, `city`, `name`

### FlightSearch Model
- Primary Key: `id` (UUIDField)
- Foreign Keys: `user`, `origin` (Airport), `destination` (Airport)
- Required fields: `search_type`, `departure_date`, `search_hash`
- Optional fields: `return_date`, `adults`, `children`, `infants`, `cabin_class`

## API Endpoints

### Airport Search
- **URL**: `/flights/api/airport-search/`
- **Method**: GET
- **Parameters**: `q` (query string, min 2 characters)
- **Returns**: JSON with airport results

### Flight Search
- **URL**: `/flights/api/flight-search/`
- **Method**: POST
- **Required fields**: `origin`, `destination`, `departure_date`, `search_type`
- **Optional fields**: `return_date`, `adults`, `children`, `infants`, `cabin_class`
- **Returns**: JSON with demo flight results (Galileo GDS integration pending)
