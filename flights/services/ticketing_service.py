import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from django.contrib.auth.models import User
from django.db import transaction
from django.core.exceptions import ValidationError

from flights.models import Booking, Ticket, PNR
from flights.services.galileo_client import galileo_client

logger = logging.getLogger(__name__)

class TicketingService:
    """
    Service for handling ticket operations using Galileo GDS
    """

    def __init__(self):
        self.galileo = galileo_client

    def issue_ticket(self, booking_id: int, user: User) -> Dict:
        """
        Issue ticket for a booking

        Args:
            booking_id: Booking ID
            user: Django user object

        Returns:
            Dict containing ticket result
        """
        try:
            booking = Booking.objects.get(id=booking_id, user=user)

            if booking.status != 'confirmed':
                raise ValidationError("Booking must be confirmed before ticketing")

            logger.info(f"Ticket issuance initiated for booking {booking_id}")

            # Prepare ticket parameters
            ticket_params = self._prepare_ticket_params(booking)

            # Call Galileo API
            api_response = self.galileo.issue_ticket(ticket_params)

            # Process response
            result = self._process_ticket_response(api_response, booking)

            logger.info(f"Ticket issued successfully for booking {booking_id}")

            return result

        except Booking.DoesNotExist:
            raise ValidationError("Booking not found")
        except Exception as e:
            logger.error(f"Ticket issuance failed: {str(e)}")
            raise ValidationError(f"Ticket issuance failed: {str(e)}")

    def void_ticket(self, ticket_number: str, user: User) -> Dict:
        """
        Void a ticket

        Args:
            ticket_number: Ticket number to void
            user: Django user object

        Returns:
            Dict containing void result
        """
        try:
            ticket = Ticket.objects.get(ticket_number=ticket_number, booking__user=user)

            logger.info(f"Ticket void initiated for {ticket_number}")

            # Call Galileo API for void (this might be a cancellation)
            api_response = self.galileo.cancel_booking(ticket.booking.pnr.pnr_number)

            # Process response
            result = self._process_void_response(api_response, ticket)

            logger.info(f"Ticket voided successfully: {ticket_number}")

            return result

        except Ticket.DoesNotExist:
            raise ValidationError("Ticket not found")
        except Exception as e:
            logger.error(f"Ticket void failed: {str(e)}")
            raise ValidationError(f"Ticket void failed: {str(e)}")

    def get_ticket_status(self, ticket_number: str, user: User) -> Dict:
        """
        Get ticket status

        Args:
            ticket_number: Ticket number
            user: Django user object

        Returns:
            Dict containing ticket status
        """
        try:
            ticket = Ticket.objects.get(ticket_number=ticket_number, booking__user=user)

            return {
                'ticket_number': ticket.ticket_number,
                'status': ticket.status,
                'issued_date': ticket.issued_date.isoformat() if ticket.issued_date else None,
                'booking_id': ticket.booking.id,
                'pnr': ticket.booking.pnr.pnr_number if ticket.booking.pnr else None
            }

        except Ticket.DoesNotExist:
            raise ValidationError("Ticket not found")

    def _prepare_ticket_params(self, booking: Booking) -> Dict:
        """Prepare parameters for ticket issuance"""
        return {
            'pnr': booking.pnr.pnr_number,
            'booking_id': booking.id,
            'passengers': [{
                'first_name': p.first_name,
                'last_name': p.last_name,
                'ticket_number': getattr(p, 'ticket_number', None)
            } for p in booking.passengers.all()],
            'total_amount': float(booking.total_amount),
            'currency': booking.currency
        }

    def _process_ticket_response(self, api_response: Dict, booking: Booking) -> Dict:
        """Process Galileo ticket response"""
        with transaction.atomic():
            # Extract ticket numbers
            ticket_numbers = self._extract_ticket_numbers(api_response)

            tickets = []
            for i, ticket_number in enumerate(ticket_numbers):
                passenger = booking.passengers.all()[i] if i < booking.passengers.count() else None

                ticket = Ticket.objects.create(
                    booking=booking,
                    ticket_number=ticket_number,
                    passenger=passenger,
                    status='issued',
                    issued_date=datetime.now(),
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

    def _process_void_response(self, api_response: Dict, ticket: Ticket) -> Dict:
        """Process Galileo void response"""
        with transaction.atomic():
            ticket.status = 'voided'
            ticket.save()

            ticket.booking.status = 'cancelled'
            ticket.booking.save()

            return {
                'success': True,
                'ticket_number': ticket.ticket_number,
                'status': 'voided'
            }

    def _extract_ticket_numbers(self, response: Dict) -> List[str]:
        """Extract ticket numbers from Galileo response"""
        # Implementation depends on API response format
        # Placeholder implementation
        return response.get('ticket_numbers', [f"TEMP_{datetime.now().strftime('%Y%m%d%H%M%S')}"])