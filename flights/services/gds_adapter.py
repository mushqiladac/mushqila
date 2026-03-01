"""
GDS Adapter - Universal Interface for Multiple GDS Systems
Supports: Galileo, Amadeus, Sabre, Worldspan
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GDSAdapter(ABC):
    """
    Abstract base class for GDS adapters
    এই interface implement করলে যেকোনো GDS সহজেই integrate করা যাবে
    """
    
    @abstractmethod
    def search_flights(self, search_params: Dict) -> Dict:
        """
        Search for flights
        
        Args:
            search_params: {
                'origin': 'JED',
                'destination': 'RUH',
                'departure_date': '2026-03-15',
                'return_date': '2026-03-20',  # optional
                'passengers': {'adult': 1, 'child': 0, 'infant': 0},
                'cabin_class': 'Economy'
            }
        
        Returns:
            {
                'success': bool,
                'itineraries': List[Dict],
                'error': str (if failed)
            }
        """
        pass
    
    @abstractmethod
    def get_fare_rules(self, fare_params: Dict) -> Dict:
        """Get fare rules for selected flight"""
        pass
    
    @abstractmethod
    def create_booking(self, booking_data: Dict) -> Dict:
        """
        Create PNR/Booking
        
        Returns:
            {
                'success': bool,
                'pnr': str,
                'booking_reference': str,
                'error': str (if failed)
            }
        """
        pass
    
    @abstractmethod
    def retrieve_booking(self, pnr: str) -> Dict:
        """Retrieve booking by PNR"""
        pass
    
    @abstractmethod
    def modify_booking(self, pnr: str, modifications: Dict) -> Dict:
        """Modify existing booking"""
        pass
    
    @abstractmethod
    def cancel_booking(self, pnr: str) -> Dict:
        """Cancel booking"""
        pass
    
    @abstractmethod
    def issue_ticket(self, ticket_data: Dict) -> Dict:
        """
        Issue ticket - THIS TRIGGERS AUTOMATED ACCOUNTING!
        
        Returns:
            {
                'success': bool,
                'ticket_numbers': List[str],
                'error': str (if failed)
            }
        """
        pass
    
    @abstractmethod
    def void_ticket(self, ticket_number: str) -> Dict:
        """Void ticket - THIS TRIGGERS VOID ACCOUNTING!"""
        pass
    
    @abstractmethod
    def refund_ticket(self, refund_data: Dict) -> Dict:
        """Process refund - THIS TRIGGERS REFUND ACCOUNTING!"""
        pass
    
    @abstractmethod
    def reissue_ticket(self, reissue_data: Dict) -> Dict:
        """Reissue/Exchange ticket"""
        pass
    
    @abstractmethod
    def get_seat_map(self, flight_data: Dict) -> Dict:
        """Get seat map for flight"""
        pass
    
    @abstractmethod
    def add_ancillary_services(self, pnr: str, services: List[Dict]) -> Dict:
        """Add ancillary services (baggage, meals, etc.)"""
        pass
    
    @abstractmethod
    def queue_place(self, pnr: str, queue_number: str) -> Dict:
        """Place PNR in queue"""
        pass
    
    @abstractmethod
    def queue_retrieve(self, queue_number: str) -> Dict:
        """Retrieve PNRs from queue"""
        pass


class GalileoAdapter(GDSAdapter):
    """
    Galileo/Travelport Universal API Adapter
    """
    
    def __init__(self):
        from .galileo_client import GalileoClient
        self.client = GalileoClient()
        self.gds_name = 'Galileo'
    
    def search_flights(self, search_params: Dict) -> Dict:
        """Search flights using Galileo API"""
        try:
            logger.info(f"[Galileo] Searching flights: {search_params}")
            
            # Call Galileo API
            response = self.client.low_fare_search(search_params)
            
            # Parse and normalize response
            itineraries = self._normalize_search_results(response)
            
            return {
                'success': True,
                'gds': self.gds_name,
                'itineraries': itineraries,
                'count': len(itineraries)
            }
            
        except Exception as e:
            logger.error(f"[Galileo] Search failed: {str(e)}")
            return {
                'success': False,
                'gds': self.gds_name,
                'error': str(e)
            }
    
    def get_fare_rules(self, fare_params: Dict) -> Dict:
        """Get fare rules from Galileo"""
        try:
            response = self.client.get_fare_rules(fare_params)
            rules = self._parse_fare_rules(response)
            
            return {
                'success': True,
                'gds': self.gds_name,
                'fare_rules': rules
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_booking(self, booking_data: Dict) -> Dict:
        """Create booking in Galileo"""
        try:
            logger.info(f"[Galileo] Creating booking")
            
            # Call Galileo API
            response = self.client.create_reservation(booking_data)
            
            # Extract PNR
            pnr = response.get('UniversalRecordLocatorCode')
            
            return {
                'success': True,
                'gds': self.gds_name,
                'pnr': pnr,
                'booking_reference': pnr,
                'raw_response': response
            }
            
        except Exception as e:
            logger.error(f"[Galileo] Booking failed: {str(e)}")
            return {
                'success': False,
                'gds': self.gds_name,
                'error': str(e)
            }
    
    def retrieve_booking(self, pnr: str) -> Dict:
        """Retrieve booking from Galileo"""
        try:
            response = self.client.retrieve_universal_record(pnr)
            booking_details = self._parse_booking_details(response)
            
            return {
                'success': True,
                'gds': self.gds_name,
                'booking': booking_details
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def modify_booking(self, pnr: str, modifications: Dict) -> Dict:
        """Modify booking in Galileo"""
        try:
            response = self.client.modify_reservation(pnr, modifications)
            
            return {
                'success': True,
                'gds': self.gds_name,
                'message': 'Booking modified successfully'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def cancel_booking(self, pnr: str) -> Dict:
        """Cancel booking in Galileo"""
        try:
            response = self.client.cancel_universal_record(pnr)
            
            return {
                'success': True,
                'gds': self.gds_name,
                'message': 'Booking cancelled successfully'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def issue_ticket(self, ticket_data: Dict) -> Dict:
        """
        Issue ticket in Galileo
        ⚠️ IMPORTANT: This triggers automated accounting!
        """
        try:
            logger.info(f"[Galileo] Issuing ticket for PNR: {ticket_data.get('pnr')}")
            
            # Call Galileo API
            response = self.client.issue_ticket(ticket_data)
            
            # Extract ticket numbers
            ticket_numbers = self._extract_ticket_numbers(response)
            
            logger.info(f"[Galileo] Tickets issued: {ticket_numbers}")
            
            return {
                'success': True,
                'gds': self.gds_name,
                'ticket_numbers': ticket_numbers,
                'raw_response': response
            }
            
        except Exception as e:
            logger.error(f"[Galileo] Ticket issuance failed: {str(e)}")
            return {
                'success': False,
                'gds': self.gds_name,
                'error': str(e)
            }
    
    def void_ticket(self, ticket_number: str) -> Dict:
        """Void ticket in Galileo"""
        try:
            response = self.client.void_ticket(ticket_number)
            
            return {
                'success': True,
                'gds': self.gds_name,
                'message': 'Ticket voided successfully'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def refund_ticket(self, refund_data: Dict) -> Dict:
        """Process refund in Galileo"""
        try:
            response = self.client.refund_ticket(refund_data)
            refund_amount = response.get('RefundAmount', 0)
            
            return {
                'success': True,
                'gds': self.gds_name,
                'refund_amount': refund_amount,
                'message': 'Refund processed successfully'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def reissue_ticket(self, reissue_data: Dict) -> Dict:
        """Reissue ticket in Galileo"""
        try:
            response = self.client.reissue_ticket(reissue_data)
            new_ticket = response.get('NewTicketNumber')
            
            return {
                'success': True,
                'gds': self.gds_name,
                'new_ticket_number': new_ticket
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_seat_map(self, flight_data: Dict) -> Dict:
        """Get seat map from Galileo"""
        try:
            response = self.client.get_seat_map(flight_data)
            seat_map = self._parse_seat_map(response)
            
            return {
                'success': True,
                'gds': self.gds_name,
                'seat_map': seat_map
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_ancillary_services(self, pnr: str, services: List[Dict]) -> Dict:
        """Add ancillary services in Galileo"""
        try:
            response = self.client.add_ancillaries(pnr, services)
            
            return {
                'success': True,
                'gds': self.gds_name,
                'message': 'Services added successfully'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def queue_place(self, pnr: str, queue_number: str) -> Dict:
        """Place PNR in queue"""
        try:
            response = self.client.queue_place(pnr, queue_number)
            
            return {
                'success': True,
                'gds': self.gds_name,
                'message': f'PNR placed in queue {queue_number}'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def queue_retrieve(self, queue_number: str) -> Dict:
        """Retrieve PNRs from queue"""
        try:
            response = self.client.queue_retrieve(queue_number)
            pnrs = self._parse_queue_response(response)
            
            return {
                'success': True,
                'gds': self.gds_name,
                'pnrs': pnrs
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # Helper methods
    def _normalize_search_results(self, response: Dict) -> List[Dict]:
        """Normalize Galileo search results to standard format"""
        # Implementation depends on Galileo response structure
        return []
    
    def _parse_fare_rules(self, response: Dict) -> Dict:
        """Parse fare rules from Galileo response"""
        return {}
    
    def _parse_booking_details(self, response: Dict) -> Dict:
        """Parse booking details from Galileo response"""
        return {}
    
    def _extract_ticket_numbers(self, response: Dict) -> List[str]:
        """Extract ticket numbers from Galileo response"""
        return []
    
    def _parse_seat_map(self, response: Dict) -> Dict:
        """Parse seat map from Galileo response"""
        return {}
    
    def _parse_queue_response(self, response: Dict) -> List[str]:
        """Parse queue response from Galileo"""
        return []


class AmadeusAdapter(GDSAdapter):
    """
    Amadeus GDS Adapter (Future implementation)
    """
    
    def __init__(self):
        self.gds_name = 'Amadeus'
        # Initialize Amadeus client
    
    def search_flights(self, search_params: Dict) -> Dict:
        return {'success': False, 'error': 'Amadeus not implemented yet'}
    
    # Implement other methods...
    def get_fare_rules(self, fare_params: Dict) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def create_booking(self, booking_data: Dict) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def retrieve_booking(self, pnr: str) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def modify_booking(self, pnr: str, modifications: Dict) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def cancel_booking(self, pnr: str) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def issue_ticket(self, ticket_data: Dict) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def void_ticket(self, ticket_number: str) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def refund_ticket(self, refund_data: Dict) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def reissue_ticket(self, reissue_data: Dict) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def get_seat_map(self, flight_data: Dict) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def add_ancillary_services(self, pnr: str, services: List[Dict]) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def queue_place(self, pnr: str, queue_number: str) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def queue_retrieve(self, queue_number: str) -> Dict:
        return {'success': False, 'error': 'Not implemented'}


class SabreAdapter(GDSAdapter):
    """
    Sabre GDS Adapter (Future implementation)
    """
    
    def __init__(self):
        self.gds_name = 'Sabre'
        # Initialize Sabre client
    
    def search_flights(self, search_params: Dict) -> Dict:
        return {'success': False, 'error': 'Sabre not implemented yet'}
    
    # Implement other methods...
    def get_fare_rules(self, fare_params: Dict) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def create_booking(self, booking_data: Dict) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def retrieve_booking(self, pnr: str) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def modify_booking(self, pnr: str, modifications: Dict) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def cancel_booking(self, pnr: str) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def issue_ticket(self, ticket_data: Dict) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def void_ticket(self, ticket_number: str) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def refund_ticket(self, refund_data: Dict) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def reissue_ticket(self, reissue_data: Dict) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def get_seat_map(self, flight_data: Dict) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def add_ancillary_services(self, pnr: str, services: List[Dict]) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def queue_place(self, pnr: str, queue_number: str) -> Dict:
        return {'success': False, 'error': 'Not implemented'}
    
    def queue_retrieve(self, queue_number: str) -> Dict:
        return {'success': False, 'error': 'Not implemented'}


# GDS Factory
class GDSFactory:
    """
    Factory class to get appropriate GDS adapter
    """
    
    _adapters = {
        'galileo': GalileoAdapter,
        'amadeus': AmadeusAdapter,
        'sabre': SabreAdapter,
    }
    
    @classmethod
    def get_adapter(cls, gds_name: str = 'galileo') -> GDSAdapter:
        """
        Get GDS adapter instance
        
        Args:
            gds_name: 'galileo', 'amadeus', or 'sabre'
        
        Returns:
            GDS adapter instance
        """
        adapter_class = cls._adapters.get(gds_name.lower())
        
        if not adapter_class:
            raise ValueError(f"Unknown GDS: {gds_name}")
        
        return adapter_class()
    
    @classmethod
    def register_adapter(cls, gds_name: str, adapter_class):
        """Register a new GDS adapter"""
        cls._adapters[gds_name.lower()] = adapter_class


# Convenience function
def get_gds_adapter(gds_name: str = 'galileo') -> GDSAdapter:
    """
    Get GDS adapter - convenience function
    
    Usage:
        gds = get_gds_adapter('galileo')
        result = gds.search_flights(params)
    """
    return GDSFactory.get_adapter(gds_name)
