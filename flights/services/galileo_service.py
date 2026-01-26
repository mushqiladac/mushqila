"""
Galileo GDS Service Layer
High-level service for flight operations using Galileo API
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from django.db import transaction
from .galileo_client import galileo_client
from ..models import Booking, Passenger, Ticket

logger = logging.getLogger(__name__)


class GalileoService:
    """Service class for Galileo GDS operations"""

    def __init__(self):
        self.client = galileo_client

    def search_flights(self, search_data: Dict) -> Dict:
        """
        Search for flights
        
        Args:
            search_data: {
                'origin': 'DAC',
                'destination': 'DXB',
                'departure_date': '2026-03-15',
                'return_date': '2026-03-20',  # optional
                'passengers': {'adult': 1, 'child': 0, 'infant': 0},
                'cabin_class': 'Economy'
            }
        
        Returns:
            Dict with flight options and pricing
        """
        try:
            logger.info(f"Searching flights: {search_data['origin']} -> {search_data['destination']}")
            
            # Call Galileo API
            response = self.client.search_flights(search_data)
            
            # Parse results
            flights = self.client.parse_search_results(response)
            
            return {
                'success': True,
                'flights': flights,
                'search_params': search_data
            }
            
        except Exception as e:
            logger.error(f"Flight search failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @transaction.atomic
    def create_booking(self, booking_data: Dict) -> Dict:
        """
        Create a new booking
        
        Args:
            booking_data: {
                'pricing_solution_key': 'xxx',
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
                'user_id': 1  # Django user ID
            }
        
        Returns:
            Dict with booking details and PNR
        """
        try:
            logger.info("Creating booking...")
            
            # Call Galileo API
            response = self.client.create_booking(booking_data)
            
            # Extract PNR and booking details
            pnr = response.get('universalRecordLocatorCode')
            
            if not pnr:
                raise Exception("PNR not received from Galileo")
            
            # Save to database
            booking = self._save_booking_to_db(response, booking_data)
            
            return {
                'success': True,
                'pnr': pnr,
                'booking_id': booking.id,
                'booking_reference': booking.booking_reference,
                'message': 'Booking created successfully'
            }
            
        except Exception as e:
            logger.error(f"Booking creation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @transaction.atomic
    def issue_ticket(self, ticket_data: Dict) -> Dict:
        """
        Issue ticket for a booking
        
        Args:
            ticket_data: {
                'booking_id': 123,
                'universal_record_locator': 'ABC123',
                'air_reservation_locator': 'XYZ789',
                'payment_info': {
                    'type': 'CreditCard',
                    'card_details': {...}
                }
            }
        
        Returns:
            Dict with ticket numbers
        """
        try:
            logger.info(f"Issuing ticket for booking: {ticket_data['booking_id']}")
            
            # Call Galileo API
            response = self.client.issue_ticket(ticket_data)
            
            # Extract ticket numbers
            ticket_numbers = self._extract_ticket_numbers(response)
            
            # Update database
            self._update_ticket_status(ticket_data['booking_id'], ticket_numbers, 'ISSUED')
            
            return {
                'success': True,
                'ticket_numbers': ticket_numbers,
                'message': 'Ticket issued successfully'
            }
            
        except Exception as e:
            logger.error(f"Ticket issuance failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @transaction.atomic
    def void_ticket(self, void_data: Dict) -> Dict:
        """
        Void a ticket (within 24 hours)
        
        Args:
            void_data: {
                'ticket_number': '1234567890123',
                'universal_record_locator': 'ABC123',
                'booking_id': 123
            }
        """
        try:
            logger.info(f"Voiding ticket: {void_data['ticket_number']}")
            
            # Call Galileo API
            response = self.client.void_ticket(void_data)
            
            # Update database
            self._update_ticket_status(void_data['booking_id'], 
                                      [void_data['ticket_number']], 
                                      'VOIDED')
            
            return {
                'success': True,
                'message': 'Ticket voided successfully'
            }
            
        except Exception as e:
            logger.error(f"Ticket void failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @transaction.atomic
    def refund_ticket(self, refund_data: Dict) -> Dict:
        """
        Process ticket refund
        
        Args:
            refund_data: {
                'ticket_number': '1234567890123',
                'universal_record_locator': 'ABC123',
                'booking_id': 123,
                'refund_type': 'Full',  # or 'Partial'
                'refund_amount': 500.00  # for partial refund
            }
        """
        try:
            logger.info(f"Processing refund for ticket: {refund_data['ticket_number']}")
            
            # Call Galileo API
            response = self.client.refund_ticket(refund_data)
            
            # Extract refund amount
            refund_amount = response.get('refundAmount', {}).get('amount', 0)
            
            # Update database
            self._update_ticket_status(refund_data['booking_id'], 
                                      [refund_data['ticket_number']], 
                                      'REFUNDED')
            
            return {
                'success': True,
                'refund_amount': refund_amount,
                'message': 'Refund processed successfully'
            }
            
        except Exception as e:
            logger.error(f"Refund processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @transaction.atomic
    def reissue_ticket(self, reissue_data: Dict) -> Dict:
        """
        Reissue/Exchange ticket
        
        Args:
            reissue_data: {
                'ticket_number': '1234567890123',
                'universal_record_locator': 'ABC123',
                'booking_id': 123,
                'new_segments': [...],
                'additional_collection': 100.00
            }
        """
        try:
            logger.info(f"Reissuing ticket: {reissue_data['ticket_number']}")
            
            # Call Galileo API
            response = self.client.reissue_ticket(reissue_data)
            
            # Extract new ticket number
            new_ticket_number = response.get('newTicketNumber')
            
            # Update database
            self._update_ticket_reissue(reissue_data['booking_id'], 
                                       reissue_data['ticket_number'],
                                       new_ticket_number)
            
            return {
                'success': True,
                'new_ticket_number': new_ticket_number,
                'message': 'Ticket reissued successfully'
            }
            
        except Exception as e:
            logger.error(f"Ticket reissue failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @transaction.atomic
    def cancel_booking(self, cancel_data: Dict) -> Dict:
        """
        Cancel a booking
        
        Args:
            cancel_data: {
                'pnr': 'ABC123',
                'booking_id': 123
            }
        """
        try:
            logger.info(f"Cancelling booking: {cancel_data['pnr']}")
            
            # Call Galileo API
            response = self.client.cancel_booking(cancel_data['pnr'])
            
            # Update database
            self._update_booking_status(cancel_data['booking_id'], 'CANCELLED')
            
            return {
                'success': True,
                'message': 'Booking cancelled successfully'
            }
            
        except Exception as e:
            logger.error(f"Booking cancellation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def retrieve_booking(self, pnr: str) -> Dict:
        """
        Retrieve booking details by PNR
        
        Args:
            pnr: Passenger Name Record number
        """
        try:
            logger.info(f"Retrieving booking: {pnr}")
            
            # Call Galileo API
            response = self.client.retrieve_pnr(pnr)
            
            # Parse booking details
            booking_details = self._parse_booking_details(response)
            
            return {
                'success': True,
                'booking': booking_details
            }
            
        except Exception as e:
            logger.error(f"Booking retrieval failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_fare_rules(self, fare_data: Dict) -> Dict:
        """
        Get fare rules for a flight
        
        Args:
            fare_data: {
                'fare_basis': 'YOWBD',
                'origin': 'DAC',
                'destination': 'DXB',
                'carrier': 'EK'
            }
        """
        try:
            logger.info(f"Fetching fare rules: {fare_data['fare_basis']}")
            
            # Call Galileo API
            response = self.client.get_fare_rules(fare_data)
            
            # Parse fare rules
            fare_rules = self._parse_fare_rules(response)
            
            return {
                'success': True,
                'fare_rules': fare_rules
            }
            
        except Exception as e:
            logger.error(f"Fare rules retrieval failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    # Helper methods for database operations
    
    def _save_booking_to_db(self, galileo_response: Dict, booking_data: Dict):
        """Save booking to database"""
        # Implementation depends on your Booking model
        # This is a placeholder
        pass

    def _update_ticket_status(self, booking_id: int, ticket_numbers: List[str], status: str):
        """Update ticket status in database"""
        # Implementation depends on your Ticket model
        pass

    def _update_ticket_reissue(self, booking_id: int, old_ticket: str, new_ticket: str):
        """Update ticket after reissue"""
        pass

    def _update_booking_status(self, booking_id: int, status: str):
        """Update booking status"""
        pass

    def _extract_ticket_numbers(self, response: Dict) -> List[str]:
        """Extract ticket numbers from Galileo response"""
        ticket_numbers = []
        # Parse response and extract ticket numbers
        return ticket_numbers

    def _parse_booking_details(self, response: Dict) -> Dict:
        """Parse booking details from Galileo response"""
        return {}

    def _parse_fare_rules(self, response: Dict) -> Dict:
        """Parse fare rules from Galileo response"""
        return {}


# Singleton instance
galileo_service = GalileoService()
