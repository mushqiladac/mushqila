import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import transaction

from flights.models import FlightSearch, FlightItinerary, Airport, Airline
from flights.services.galileo_client import galileo_client

logger = logging.getLogger(__name__)

class FlightSearchService:
    """
    Service for handling flight search operations using Galileo GDS
    """

    def __init__(self):
        self.galileo = galileo_client

    def search_flights(self, user: User, search_data: Dict) -> Dict:
        """
        Search for flights using Galileo API

        Args:
            user: Django user object
            search_data: Search parameters from form

        Returns:
            Dict containing search results
        """
        try:
            # Log search attempt
            logger.info(f"Flight search initiated by user {user.username}: {search_data}")

            # Save search to database
            search_record = self._save_search_record(user, search_data)

            # Prepare Galileo API parameters
            api_params = self._prepare_api_params(search_data)

            # Call Galileo API
            api_response = self.galileo.search_flights(api_params)

            # Parse and format results
            results = self._process_search_results(api_response, search_record)

            # Update search record with results count
            search_record.result_count = results.get('count', 0)
            search_record.save()

            logger.info(f"Search completed for user {user.username}: {results.get('count', 0)} results")

            return results

        except Exception as e:
            logger.error(f"Flight search failed for user {user.username}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'results': [],
                'count': 0
            }

    def _prepare_api_params(self, search_data: Dict) -> Dict:
        """Convert form data to Galileo API parameters"""
        params = {
            'origin': search_data['origin'],
            'destination': search_data['destination'],
            'departure_date': search_data['departure_date'].strftime('%Y-%m-%d'),
            'passengers': {
                'adult': search_data.get('adults', 1),
                'child': search_data.get('children', 0),
                'infant': search_data.get('infants', 0)
            }
        }

        # Add return date for round trip
        if search_data.get('return_date'):
            params['return_date'] = search_data['return_date'].strftime('%Y-%m-%d')

        # Add cabin class
        if search_data.get('cabin_class'):
            cabin_map = {
                'economy': 'Economy',
                'premium_economy': 'PremiumEconomy',
                'business': 'Business',
                'first': 'First'
            }
            params['cabin_class'] = cabin_map.get(search_data['cabin_class'], 'Economy')

        return params

    def _process_search_results(self, api_response: Dict, search_record: FlightSearch) -> Dict:
        """Process Galileo API response into standardized format"""
        try:
            # Parse flights from Galileo response
            flights = self.galileo.parse_search_results(api_response)

            # Save itineraries to database
            saved_itineraries = self._save_itineraries(flights, search_record)

            return {
                'success': True,
                'results': saved_itineraries,
                'count': len(saved_itineraries),
                'search_id': search_record.id
            }

        except Exception as e:
            logger.error(f"Error processing search results: {str(e)}")
            return {
                'success': False,
                'error': f"Error processing results: {str(e)}",
                'results': [],
                'count': 0
            }

    def _save_search_record(self, user: User, search_data: Dict) -> FlightSearch:
        """Save search record to database"""
        return FlightSearch.objects.create(
            user=user,
            origin=search_data['origin'],
            destination=search_data['destination'],
            departure_date=search_data['departure_date'],
            return_date=search_data.get('return_date'),
            adults=search_data.get('adults', 1),
            children=search_data.get('children', 0),
            infants=search_data.get('infants', 0),
            cabin_class=search_data.get('cabin_class', 'economy'),
            search_type=search_data.get('trip_type', 'one_way')
        )

    def _save_itineraries(self, flights: List[Dict], search_record: FlightSearch) -> List[Dict]:
        """Save flight itineraries to database"""
        saved_itineraries = []

        for flight in flights:
            try:
                itinerary = FlightItinerary.objects.create(
                    search=search_record,
                    airline_code=flight.get('airline', ''),
                    flight_number=flight.get('flight_number', ''),
                    departure_airport=flight.get('origin', ''),
                    arrival_airport=flight.get('destination', ''),
                    departure_time=flight.get('departure_time'),
                    arrival_time=flight.get('arrival_time'),
                    duration=flight.get('duration', ''),
                    stops=flight.get('stops', 0),
                    price=flight.get('price', 0),
                    currency=flight.get('currency', 'USD'),
                    cabin_class=flight.get('cabin_class', ''),
                    fare_basis=flight.get('fare_basis', ''),
                    raw_data=flight  # Store complete API response
                )
                saved_itineraries.append({
                    'id': itinerary.id,
                    'airline': itinerary.airline_code,
                    'flight_number': itinerary.flight_number,
                    'departure': {
                        'airport': itinerary.departure_airport,
                        'time': itinerary.departure_time.isoformat() if itinerary.departure_time else None
                    },
                    'arrival': {
                        'airport': itinerary.arrival_airport,
                        'time': itinerary.arrival_time.isoformat() if itinerary.arrival_time else None
                    },
                    'duration': itinerary.duration,
                    'stops': itinerary.stops,
                    'price': float(itinerary.price),
                    'currency': itinerary.currency,
                    'cabin_class': itinerary.cabin_class
                })

            except Exception as e:
                logger.error(f"Error saving itinerary: {str(e)}")
                continue

        return saved_itineraries

    def get_search_results(self, search_id: int) -> Optional[Dict]:
        """Retrieve saved search results"""
        try:
            search = FlightSearch.objects.get(id=search_id)
            itineraries = FlightItinerary.objects.filter(search=search)

            return {
                'search': {
                    'id': search.id,
                    'origin': search.origin,
                    'destination': search.destination,
                    'departure_date': search.departure_date.isoformat(),
                    'return_date': search.return_date.isoformat() if search.return_date else None,
                    'adults': search.adults,
                    'children': search.children,
                    'infants': search.infants,
                    'cabin_class': search.cabin_class
                },
                'results': [{
                    'id': it.id,
                    'airline': it.airline_code,
                    'flight_number': it.flight_number,
                    'departure': {
                        'airport': it.departure_airport,
                        'time': it.departure_time.isoformat() if it.departure_time else None
                    },
                    'arrival': {
                        'airport': it.arrival_airport,
                        'time': it.arrival_time.isoformat() if it.arrival_time else None
                    },
                    'duration': it.duration,
                    'stops': it.stops,
                    'price': float(it.price),
                    'currency': it.currency,
                    'cabin_class': it.cabin_class
                } for it in itineraries]
            }

        except FlightSearch.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error retrieving search results: {str(e)}")
            return None