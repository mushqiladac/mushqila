# flights/models/__init__.py

# Core flight models
from .flight_models import (
    Airline,
    Airport,
    Aircraft,
    FlightSearch,
    FlightSegment,
    FlightItinerary,
    ItinerarySegment,
    FareRule,
    BaggageRule,
)

# Booking and reservation models
from .booking_models import (
    Passenger,
    Booking,
    BookingPassenger,
    BookingHistory,
    PNR,
    Ticket,
    Payment,
    Refund,
)

# Fare rules and pricing models
from .fare_models import (
    Fare,
    FareComponent,
    Tax,
    CommissionRule,
    MarkupRule,
    CorporateFare,
    PromoCode,
)

# Ancillary services models
from .ancillary_models import (
    AncillaryService,
    SeatSelection,
    MealPreference,
    BaggageService,
    TravelInsurance,
    LoungeAccess,
    AncillaryBooking,
)

# Inventory management models
from .inventory_models import (
    FlightInventory,
    SeatInventory,
    FareBucket,
    AvailabilityCache,
    BookingLimit,
    OverrideRule,
)

# Explicit exports
__all__ = [
    # Core flight models
    'Airline',
    'Airport',
    'Aircraft',
    'FlightSearch',
    'FlightSegment',
    'FlightItinerary',
    'ItinerarySegment',
    'FareRule',
    'BaggageRule',
    
    # Booking models
    'Passenger',
    'Booking',
    'BookingPassenger',
    'BookingHistory',
    'PNR',
    'Ticket',
    'Payment',
    'Refund',
    
    # Fare models
    'Fare',
    'FareComponent',
    'Tax',
    'CommissionRule',
    'MarkupRule',
    'CorporateFare',
    'PromoCode',
    
    # Ancillary models
    'AncillaryService',
    'SeatSelection',
    'MealPreference',
    'BaggageService',
    'TravelInsurance',
    'LoungeAccess',
    'AncillaryBooking',
    
    # Inventory models
    'FlightInventory',
    'SeatInventory',
    'FareBucket',
    'AvailabilityCache',
    'BookingLimit',
    'OverrideRule',
]