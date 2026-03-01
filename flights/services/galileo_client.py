"""
Galileo/Travelport Universal API Client
Low-level SOAP client for Galileo GDS
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)

# Check if zeep is available
try:
    from zeep import Client, Settings
    from zeep.transports import Transport
    from zeep.exceptions import Fault
    from requests import Session
    from requests.auth import HTTPBasicAuth
    ZEEP_AVAILABLE = True
except ImportError:
    ZEEP_AVAILABLE = False
    logger.warning("zeep library not installed. Install with: pip install zeep")


class GalileoClient:
    """
    Low-level Galileo API client using SOAP/XML
    """
    
    def __init__(self):
        """Initialize Galileo client with credentials from environment"""
        
        # Get credentials from environment
        self.pcc = os.getenv('GALILEO_PCC', '')
        self.username = os.getenv('GALILEO_USERNAME', '')
        self.password = os.getenv('GALILEO_PASSWORD', '')
        self.target_branch = os.getenv('GALILEO_TARGET_BRANCH', '')
        self.provider_code = os.getenv('GALILEO_PROVIDER_CODE', '1G')
        
        # API endpoints
        self.air_endpoint = os.getenv(
            'GALILEO_AIR_ENDPOINT',
            'https://apac.universal-api.travelport.com/B2BGateway/connect/uAPI/AirService'
        )
        self.universal_endpoint = os.getenv(
            'GALILEO_UNIVERSAL_ENDPOINT',
            'https://apac.universal-api.travelport.com/B2BGateway/connect/uAPI/UniversalRecordService'
        )
        self.util_endpoint = os.getenv(
            'GALILEO_UTIL_ENDPOINT',
            'https://apac.universal-api.travelport.com/B2BGateway/connect/uAPI/UtilService'
        )
        
        # WSDL URLs
        self.air_wsdl = os.getenv(
            'GALILEO_AIR_WSDL',
            'https://support.travelport.com/webhelp/uapi/uAPI_AirService.wsdl'
        )
        self.universal_wsdl = os.getenv(
            'GALILEO_UNIVERSAL_WSDL',
            'https://support.travelport.com/webhelp/uapi/uAPI_UniversalRecordService.wsdl'
        )
        
        # Initialize SOAP clients if zeep is available
        if ZEEP_AVAILABLE and self.username and self.password:
            self._init_soap_clients()
        else:
            logger.warning("Galileo client not fully initialized. Check credentials and zeep installation.")
            self.air_client = None
            self.universal_client = None
    
    def _init_soap_clients(self):
        """Initialize SOAP clients with authentication"""
        try:
            # Setup session with authentication
            session = Session()
            session.auth = HTTPBasicAuth(self.username, self.password)
            
            # Setup transport
            transport = Transport(session=session, timeout=30)
            
            # Setup settings
            settings = Settings(strict=False, xml_huge_tree=True)
            
            # Create SOAP clients
            self.air_client = Client(
                self.air_wsdl,
                transport=transport,
                settings=settings
            )
            
            self.universal_client = Client(
                self.universal_wsdl,
                transport=transport,
                settings=settings
            )
            
            logger.info("Galileo SOAP clients initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Galileo clients: {str(e)}")
            self.air_client = None
            self.universal_client = None
    
    def _get_billing_point_of_sale(self) -> Dict:
        """Get billing point of sale info"""
        return {
            'OriginApplication': 'UAPI',
            'TargetBranch': self.target_branch
        }
    
    def low_fare_search(self, search_params: Dict) -> Dict:
        """
        Low fare search
        
        Args:
            search_params: {
                'origin': 'JED',
                'destination': 'RUH',
                'departure_date': '2026-03-15',
                'return_date': '2026-03-20',  # optional
                'passengers': {'adult': 1, 'child': 0, 'infant': 0},
                'cabin_class': 'Economy'
            }
        """
        if not self.air_client:
            raise Exception("Galileo client not initialized")
        
        try:
            # Build search request
            search_air_legs = []
            
            # Outbound leg
            search_air_legs.append({
                'SearchOrigin': [{'Airport': {'Code': search_params['origin']}}],
                'SearchDestination': [{'Airport': {'Code': search_params['destination']}}],
                'SearchDepTime': search_params['departure_date']
            })
            
            # Return leg if round trip
            if search_params.get('return_date'):
                search_air_legs.append({
                    'SearchOrigin': [{'Airport': {'Code': search_params['destination']}}],
                    'SearchDestination': [{'Airport': {'Code': search_params['origin']}}],
                    'SearchDepTime': search_params['return_date']
                })
            
            # Build passenger list
            search_passengers = []
            passengers = search_params.get('passengers', {'adult': 1, 'child': 0, 'infant': 0})
            
            for _ in range(passengers.get('adult', 1)):
                search_passengers.append({'Code': 'ADT', 'Age': 30})
            
            for _ in range(passengers.get('child', 0)):
                search_passengers.append({'Code': 'CNN', 'Age': 10})
            
            for _ in range(passengers.get('infant', 0)):
                search_passengers.append({'Code': 'INF', 'Age': 1})
            
            # Call Galileo API
            response = self.air_client.service.LowFareSearchReq(
                BillingPointOfSaleInfo=self._get_billing_point_of_sale(),
                SearchAirLeg=search_air_legs,
                SearchPassenger=search_passengers,
                AirSearchModifiers={
                    'PreferredCabins': [{'CabinClass': search_params.get('cabin_class', 'Economy')}]
                }
            )
            
            return response
            
        except Fault as fault:
            logger.error(f"Galileo SOAP Fault: {fault}")
            raise Exception(f"Galileo API Error: {fault.message}")
        except Exception as e:
            logger.error(f"Galileo search error: {str(e)}")
            raise
    
    def create_reservation(self, booking_data: Dict) -> Dict:
        """
        Create air reservation (PNR)
        
        Args:
            booking_data: {
                'pricing_solution': {...},  # From search results
                'passengers': [...],
                'contact_info': {...}
            }
        """
        if not self.universal_client:
            raise Exception("Galileo client not initialized")
        
        try:
            # Build booking travelers
            booking_travelers = []
            
            for idx, passenger in enumerate(booking_data['passengers']):
                traveler = {
                    'Key': f'Traveler_{idx}',
                    'TravelerType': passenger['type'],
                    'BookingTravelerName': {
                        'Prefix': passenger.get('title', 'MR'),
                        'First': passenger['first_name'],
                        'Last': passenger['last_name']
                    },
                    'DOB': passenger.get('date_of_birth', ''),
                    'Gender': passenger.get('gender', 'M')
                }
                
                # Add contact info
                if passenger.get('email'):
                    traveler['Email'] = [{
                        'Type': 'Primary',
                        'EmailID': passenger['email']
                    }]
                
                if passenger.get('phone'):
                    traveler['PhoneNumber'] = [{
                        'Type': 'Mobile',
                        'Number': passenger['phone']
                    }]
                
                # Add passport info if available
                if passenger.get('passport_number'):
                    traveler['SSR'] = [{
                        'Type': 'DOCS',
                        'FreeText': self._format_docs_ssr(passenger)
                    }]
                
                booking_travelers.append(traveler)
            
            # Call Galileo API
            response = self.universal_client.service.AirCreateReservationReq(
                BillingPointOfSaleInfo=self._get_billing_point_of_sale(),
                BookingTraveler=booking_travelers,
                AirPricingSolution=booking_data['pricing_solution'],
                ActionStatus={
                    'Type': 'TAW',
                    'TicketDate': (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d'),
                    'ProviderCode': self.provider_code
                }
            )
            
            return response
            
        except Fault as fault:
            logger.error(f"Galileo SOAP Fault: {fault}")
            raise Exception(f"Galileo API Error: {fault.message}")
        except Exception as e:
            logger.error(f"Galileo booking error: {str(e)}")
            raise
    
    def retrieve_universal_record(self, pnr: str) -> Dict:
        """Retrieve universal record by PNR"""
        if not self.universal_client:
            raise Exception("Galileo client not initialized")
        
        try:
            response = self.universal_client.service.UniversalRecordRetrieveReq(
                BillingPointOfSaleInfo=self._get_billing_point_of_sale(),
                UniversalRecordLocatorCode=pnr
            )
            
            return response
            
        except Fault as fault:
            logger.error(f"Galileo SOAP Fault: {fault}")
            raise Exception(f"Galileo API Error: {fault.message}")
        except Exception as e:
            logger.error(f"Galileo retrieve error: {str(e)}")
            raise
    
    def issue_ticket(self, ticket_data: Dict) -> Dict:
        """
        Issue ticket
        
        Args:
            ticket_data: {
                'pnr': 'ABC123',
                'air_reservation_locator': 'XYZ789',
                'payment_info': {...}
            }
        """
        if not self.air_client:
            raise Exception("Galileo client not initialized")
        
        try:
            # Build form of payment
            form_of_payment = {
                'Type': ticket_data['payment_info'].get('type', 'Cash')
            }
            
            if ticket_data['payment_info'].get('type') == 'CreditCard':
                form_of_payment['CreditCard'] = ticket_data['payment_info']['card_details']
            
            # Call Galileo API
            response = self.air_client.service.AirTicketingReq(
                BillingPointOfSaleInfo=self._get_billing_point_of_sale(),
                AirReservationLocatorCode=ticket_data['air_reservation_locator'],
                FormOfPayment=form_of_payment,
                Commission={
                    'Type': 'PercentBase',
                    'Value': '10.00'
                }
            )
            
            return response
            
        except Fault as fault:
            logger.error(f"Galileo SOAP Fault: {fault}")
            raise Exception(f"Galileo API Error: {fault.message}")
        except Exception as e:
            logger.error(f"Galileo ticketing error: {str(e)}")
            raise
    
    def void_ticket(self, ticket_number: str) -> Dict:
        """Void ticket"""
        if not self.air_client:
            raise Exception("Galileo client not initialized")
        
        try:
            response = self.air_client.service.AirVoidDocumentReq(
                BillingPointOfSaleInfo=self._get_billing_point_of_sale(),
                AirTicketNumber=ticket_number,
                ProviderCode=self.provider_code
            )
            
            return response
            
        except Fault as fault:
            logger.error(f"Galileo SOAP Fault: {fault}")
            raise Exception(f"Galileo API Error: {fault.message}")
        except Exception as e:
            logger.error(f"Galileo void error: {str(e)}")
            raise
    
    def refund_ticket(self, refund_data: Dict) -> Dict:
        """Process ticket refund"""
        if not self.air_client:
            raise Exception("Galileo client not initialized")
        
        try:
            response = self.air_client.service.AirRefundReq(
                BillingPointOfSaleInfo=self._get_billing_point_of_sale(),
                AirTicketNumber=refund_data['ticket_number'],
                RefundType=refund_data.get('refund_type', 'Full').upper(),
                ProviderCode=self.provider_code
            )
            
            return response
            
        except Fault as fault:
            logger.error(f"Galileo SOAP Fault: {fault}")
            raise Exception(f"Galileo API Error: {fault.message}")
        except Exception as e:
            logger.error(f"Galileo refund error: {str(e)}")
            raise
    
    def reissue_ticket(self, reissue_data: Dict) -> Dict:
        """Reissue/Exchange ticket"""
        if not self.air_client:
            raise Exception("Galileo client not initialized")
        
        try:
            response = self.air_client.service.AirExchangeReq(
                BillingPointOfSaleInfo=self._get_billing_point_of_sale(),
                AirTicketNumber=reissue_data['ticket_number'],
                NewSegments=reissue_data.get('new_segments', []),
                ProviderCode=self.provider_code
            )
            
            return response
            
        except Fault as fault:
            logger.error(f"Galileo SOAP Fault: {fault}")
            raise Exception(f"Galileo API Error: {fault.message}")
        except Exception as e:
            logger.error(f"Galileo reissue error: {str(e)}")
            raise
    
    def cancel_universal_record(self, pnr: str) -> Dict:
        """Cancel universal record"""
        if not self.universal_client:
            raise Exception("Galileo client not initialized")
        
        try:
            response = self.universal_client.service.UniversalRecordCancelReq(
                BillingPointOfSaleInfo=self._get_billing_point_of_sale(),
                UniversalRecordLocatorCode=pnr
            )
            
            return response
            
        except Fault as fault:
            logger.error(f"Galileo SOAP Fault: {fault}")
            raise Exception(f"Galileo API Error: {fault.message}")
        except Exception as e:
            logger.error(f"Galileo cancel error: {str(e)}")
            raise
    
    def get_fare_rules(self, fare_data: Dict) -> Dict:
        """Get fare rules"""
        if not self.air_client:
            raise Exception("Galileo client not initialized")
        
        try:
            response = self.air_client.service.AirFareRulesReq(
                BillingPointOfSaleInfo=self._get_billing_point_of_sale(),
                FareBasis=fare_data['fare_basis'],
                Origin=fare_data['origin'],
                Destination=fare_data['destination'],
                Carrier=fare_data['carrier']
            )
            
            return response
            
        except Fault as fault:
            logger.error(f"Galileo SOAP Fault: {fault}")
            raise Exception(f"Galileo API Error: {fault.message}")
        except Exception as e:
            logger.error(f"Galileo fare rules error: {str(e)}")
            raise
    
    def get_seat_map(self, flight_data: Dict) -> Dict:
        """Get seat map for flight"""
        if not self.air_client:
            raise Exception("Galileo client not initialized")
        
        try:
            response = self.air_client.service.SeatMapReq(
                BillingPointOfSaleInfo=self._get_billing_point_of_sale(),
                AirSegment=flight_data['segment']
            )
            
            return response
            
        except Fault as fault:
            logger.error(f"Galileo SOAP Fault: {fault}")
            raise Exception(f"Galileo API Error: {fault.message}")
        except Exception as e:
            logger.error(f"Galileo seat map error: {str(e)}")
            raise
    
    def add_ancillaries(self, pnr: str, services: List[Dict]) -> Dict:
        """Add ancillary services"""
        if not self.universal_client:
            raise Exception("Galileo client not initialized")
        
        try:
            response = self.universal_client.service.UniversalRecordModifyReq(
                BillingPointOfSaleInfo=self._get_billing_point_of_sale(),
                UniversalRecordLocatorCode=pnr,
                AncillaryServices=services
            )
            
            return response
            
        except Fault as fault:
            logger.error(f"Galileo SOAP Fault: {fault}")
            raise Exception(f"Galileo API Error: {fault.message}")
        except Exception as e:
            logger.error(f"Galileo ancillary error: {str(e)}")
            raise
    
    def queue_place(self, pnr: str, queue_number: str) -> Dict:
        """Place PNR in queue"""
        if not self.universal_client:
            raise Exception("Galileo client not initialized")
        
        try:
            response = self.universal_client.service.QueuePlaceReq(
                BillingPointOfSaleInfo=self._get_billing_point_of_sale(),
                UniversalRecordLocatorCode=pnr,
                QueueNumber=queue_number
            )
            
            return response
            
        except Fault as fault:
            logger.error(f"Galileo SOAP Fault: {fault}")
            raise Exception(f"Galileo API Error: {fault.message}")
        except Exception as e:
            logger.error(f"Galileo queue place error: {str(e)}")
            raise
    
    def queue_retrieve(self, queue_number: str) -> Dict:
        """Retrieve PNRs from queue"""
        if not self.universal_client:
            raise Exception("Galileo client not initialized")
        
        try:
            response = self.universal_client.service.QueueRetrieveReq(
                BillingPointOfSaleInfo=self._get_billing_point_of_sale(),
                QueueNumber=queue_number
            )
            
            return response
            
        except Fault as fault:
            logger.error(f"Galileo SOAP Fault: {fault}")
            raise Exception(f"Galileo API Error: {fault.message}")
        except Exception as e:
            logger.error(f"Galileo queue retrieve error: {str(e)}")
            raise
    
    def _format_docs_ssr(self, passenger: Dict) -> str:
        """Format DOCS SSR for passport information"""
        return (
            f"P/{passenger['nationality']}/{passenger['passport_number']}/"
            f"{passenger['nationality']}/{passenger['date_of_birth'].strftime('%d%b%y')}/"
            f"{passenger['gender']}/{passenger['passport_expiry'].strftime('%d%b%y')}/"
            f"{passenger['last_name']}/{passenger['first_name']}"
        )


# Singleton instance
galileo_client = GalileoClient()
