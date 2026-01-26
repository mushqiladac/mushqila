import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from django.contrib.auth.models import User
from django.db import transaction
from django.core.exceptions import ValidationError

from flights.models import Booking, Passenger, FlightItinerary, PNR, Payment
from flights.services.galileo_client import galileo_client

logger = logging.getLogger(__name__)

class BookingService:
    """
    Service for handling flight booking operations using Galileo GDS
    """

    def __init__(self):
        self.galileo = galileo_client

    def create_booking(self, user: User, booking_data: Dict) -> Dict:
        """
        Create a flight booking using Galileo API

        Args:
            user: Django user object
            booking_data: Booking parameters

        Returns:
            Dict containing booking result
        """
        try:
            logger.info(f"Booking creation initiated by user {user.username}")

            # Validate booking data
            self._validate_booking_data(booking_data)

            # Prepare Galileo booking parameters
            api_params = self._prepare_booking_params(booking_data)

            # Call Galileo API to create booking
            api_response = self.galileo.create_booking(api_params)

            # Process booking response
            booking_result = self._process_booking_response(api_response, user, booking_data)

            logger.info(f"Booking created successfully for user {user.username}: {booking_result.get('pnr')}")

            return booking_result

        except Exception as e:
            logger.error(f"Booking creation failed for user {user.username}: {str(e)}")
            raise ValidationError(f"Booking failed: {str(e)}")

    def cancel_booking(self, pnr: str, user: User) -> Dict:
        """
        Cancel a booking using Galileo API

        Args:
            pnr: Passenger Name Record
            user: Django user object

        Returns:
            Dict containing cancellation result
        """
        try:
            logger.info(f"Booking cancellation initiated for PNR {pnr} by user {user.username}")

            # Call Galileo API to cancel booking
            api_response = self.galileo.cancel_booking(pnr)

            # Process cancellation response
            cancel_result = self._process_cancellation_response(api_response, pnr)

            logger.info(f"Booking cancelled successfully for PNR {pnr}")

            return cancel_result

        except Exception as e:
            logger.error(f"Booking cancellation failed for PNR {pnr}: {str(e)}")
            raise ValidationError(f"Cancellation failed: {str(e)}")

    def issue_ticket(self, booking_id: int, user: User) -> Dict:
        """
        Issue ticket for a booking using Galileo API

        Args:
            booking_id: Booking ID
            user: Django user object

        Returns:
            Dict containing ticket result
        """
        try:
            # Get booking
            booking = Booking.objects.get(id=booking_id, user=user)
            pnr = booking.pnr.pnr_number if booking.pnr else None

            if not pnr:
                raise ValidationError("No PNR found for booking")

            logger.info(f"Ticket issuance initiated for booking {booking_id}, PNR {pnr}")

            # Prepare ticket parameters
            ticket_params = self._prepare_ticket_params(booking)

            # Call Galileo API to issue ticket
            api_response = self.galileo.issue_ticket(ticket_params)

            # Process ticket response
            ticket_result = self._process_ticket_response(api_response, booking)

            logger.info(f"Ticket issued successfully for booking {booking_id}")

            return ticket_result

        except Booking.DoesNotExist:
            raise ValidationError("Booking not found")
        except Exception as e:
            logger.error(f"Ticket issuance failed for booking {booking_id}: {str(e)}")
            raise ValidationError(f"Ticket issuance failed: {str(e)}")

    def _validate_booking_data(self, data: Dict):
        """Validate booking data before processing"""
        required_fields = ['itinerary_id', 'passengers', 'contact_info']

        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        if not data.get('passengers'):
            raise ValidationError("At least one passenger is required")

        # Validate passenger data
        for passenger in data['passengers']:
            if not all(k in passenger for k in ['first_name', 'last_name', 'date_of_birth']):
                raise ValidationError("Incomplete passenger information")

    def _prepare_booking_params(self, data: Dict) -> Dict:
        """Prepare parameters for Galileo booking API"""
        itinerary = FlightItinerary.objects.get(id=data['itinerary_id'])

        params = {
            'itinerary': {
                'airline': itinerary.airline_code,
                'flight_number': itinerary.flight_number,
                'origin': itinerary.departure_airport,
                'destination': itinerary.arrival_airport,
                'departure_date': itinerary.departure_time.strftime('%Y-%m-%d'),
                'departure_time': itinerary.departure_time.strftime('%H:%M'),
            },
            'passengers': data['passengers'],
            'contact_info': data['contact_info']
        }

        return params

    def _process_booking_response(self, api_response: Dict, user: User, booking_data: Dict) -> Dict:
        """Process Galileo booking response and save to database"""
        with transaction.atomic():
            # Extract PNR from response
            pnr_number = self._extract_pnr_from_response(api_response)

            # Create PNR record
            pnr = PNR.objects.create(
                pnr_number=pnr_number,
                raw_response=api_response
            )

            # Create booking
            itinerary = FlightItinerary.objects.get(id=booking_data['itinerary_id'])
            booking = Booking.objects.create(
                user=user,
                itinerary=itinerary,
                pnr=pnr,
                status='confirmed',
                total_amount=itinerary.price,
                currency=itinerary.currency
            )

            # Create passenger records
            for passenger_data in booking_data['passengers']:
                Passenger.objects.create(
                    booking=booking,
                    first_name=passenger_data['first_name'],
                    last_name=passenger_data['last_name'],
                    date_of_birth=passenger_data['date_of_birth'],
                    gender=passenger_data.get('gender'),
                    passport_number=passenger_data.get('passport_number'),
                    nationality=passenger_data.get('nationality')
                )

            return {
                'success': True,
                'booking_id': booking.id,
                'pnr': pnr_number,
                'status': 'confirmed'
            }

    def _process_cancellation_response(self, api_response: Dict, pnr: str) -> Dict:
        """Process Galileo cancellation response"""
        # Update booking status in database
        try:
            booking = Booking.objects.get(pnr__pnr_number=pnr)
            booking.status = 'cancelled'
            booking.save()

            return {
                'success': True,
                'pnr': pnr,
                'status': 'cancelled'
            }
        except Booking.DoesNotExist:
            raise ValidationError("Booking not found for PNR")

    def _process_ticket_response(self, api_response: Dict, booking: Booking) -> Dict:
        """Process Galileo ticket response"""
        # Extract ticket numbers from response
        ticket_numbers = self._extract_tickets_from_response(api_response)

        # Create ticket records
        tickets = []
        for ticket_number in ticket_numbers:
            ticket = Ticket.objects.create(
                booking=booking,
                ticket_number=ticket_number,
                status='issued',
                raw_response=api_response
            )
            tickets.append(ticket_number)

        # Update booking status
        booking.status = 'ticketed'
        booking.save()

        return {
            'success': True,
            'booking_id': booking.id,
            'tickets': tickets,
            'status': 'ticketed'
        }

    def _prepare_ticket_params(self, booking: Booking) -> Dict:
        """Prepare parameters for ticket issuance"""
        return {
            'pnr': booking.pnr.pnr_number,
            'passengers': [{
                'first_name': p.first_name,
                'last_name': p.last_name
            } for p in booking.passengers.all()]
        }

    def _extract_pnr_from_response(self, response: Dict) -> str:
        """Extract PNR from Galileo booking response"""
        # Implementation depends on Galileo API response format
        # This is a placeholder
        return response.get('pnr', 'TEMP_PNR')

    def _extract_tickets_from_response(self, response: Dict) -> List[str]:
        """Extract ticket numbers from Galileo ticket response"""
        # Implementation depends on Galileo API response format
        # This is a placeholder
        return response.get('ticket_numbers', ['TEMP_TICKET'])