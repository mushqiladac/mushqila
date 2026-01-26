import requests
import json
import logging
from datetime import datetime
from django.conf import settings
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class GalileoAPIClient:
    """
    Travelport Galileo GDS API Client
    Handles authentication and API calls to Galileo system
    """

    def __init__(self):
        self.username = settings.TRAVELPORT_USERNAME
        self.password = settings.TRAVELPORT_PASSWORD
        self.branch_code = settings.TRAVELPORT_BRANCH_CODE
        self.target_branch = settings.TRAVELPORT_TARGET_BRANCH
        self.base_url = settings.TRAVELPORT_BASE_URL
        self.rest_url = settings.TRAVELPORT_REST_URL
        self.session_token = None
        self.token_expiry = None

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {self._get_basic_auth()}'
        }

    def _get_basic_auth(self) -> str:
        """Generate basic auth string"""
        import base64
        auth_string = f"{self.username}:{self.password}"
        return base64.b64encode(auth_string.encode()).decode()

    def _make_request(self, endpoint: str, payload: Dict, method: str = 'POST') -> Dict:
        """Make HTTP request to Galileo API"""
        url = f"{self.rest_url}/{endpoint}"

        try:
            headers = self._get_auth_headers()
            response = requests.request(method, url, json=payload, headers=headers, timeout=30)

            logger.info(f"Galileo API Request: {method} {url}")
            logger.debug(f"Request Payload: {json.dumps(payload, indent=2)}")

            response.raise_for_status()
            result = response.json()

            logger.info(f"Galileo API Response Status: {response.status_code}")
            logger.debug(f"Response: {json.dumps(result, indent=2)}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Galileo API request failed: {str(e)}")
            raise Exception(f"Galileo API Error: {str(e)}")

    def search_flights(self, search_params: Dict) -> Dict:
        """
        Search for available flights

        Args:
            search_params: Dict containing:
                - origin: str (airport code)
                - destination: str (airport code)
                - departure_date: str (YYYY-MM-DD)
                - return_date: str (YYYY-MM-DD) optional
                - passengers: Dict with adult, child, infant counts
                - cabin_class: str (Economy, PremiumEconomy, Business, First)
        """
        payload = self._build_search_payload(search_params)
        return self._make_request('AirLowFareSearchReq', payload)

    def get_availability(self, availability_params: Dict) -> Dict:
        """
        Get detailed availability for specific flights

        Args:
            availability_params: Dict containing flight details
        """
        payload = self._build_availability_payload(availability_params)
        return self._make_request('AirAvailabilitySearchReq', payload)

    def create_booking(self, booking_params: Dict) -> Dict:
        """
        Create a flight booking

        Args:
            booking_params: Dict containing booking details
        """
        payload = self._build_booking_payload(booking_params)
        return self._make_request('AirBookReq', payload)

    def cancel_booking(self, pnr: str) -> Dict:
        """
        Cancel a booking

        Args:
            pnr: Passenger Name Record number
        """
        payload = self._build_cancel_payload(pnr)
        return self._make_request('AirCancelReq', payload)

    def issue_ticket(self, ticket_params: Dict) -> Dict:
        """
        Issue ticket for a booking

        Args:
            ticket_params: Dict containing ticket details
        """
        payload = self._build_ticket_payload(ticket_params)
        return self._make_request('AirTicketReq', payload)

    def void_ticket(self, void_params: Dict) -> Dict:
        """
        Void a ticket (must be done within 24 hours of issuance)
        
        Args:
            void_params: Dict containing:
                - ticket_number: str
                - universal_record_locator: str (PNR)
        """
        payload = {
            "targetBranch": self.target_branch,
            "universalRecordLocatorCode": void_params['universal_record_locator'],
            "ticketNumber": void_params['ticket_number'],
            "voidType": "Full"
        }
        return self._make_request('AirVoidDocumentReq', payload)

    def refund_ticket(self, refund_params: Dict) -> Dict:
        """
        Process ticket refund
        
        Args:
            refund_params: Dict containing:
                - ticket_number: str
                - universal_record_locator: str (PNR)
                - refund_type: str (Full/Partial)
                - refund_amount: float (for partial refund)
        """
        payload = {
            "targetBranch": self.target_branch,
            "universalRecordLocatorCode": refund_params['universal_record_locator'],
            "ticketNumber": refund_params['ticket_number'],
            "refundType": refund_params.get('refund_type', 'Full')
        }
        
        if refund_params.get('refund_amount'):
            payload['refundAmount'] = {
                "amount": refund_params['refund_amount'],
                "currency": refund_params.get('currency', 'USD')
            }
        
        return self._make_request('AirRefundReq', payload)

    def reissue_ticket(self, reissue_params: Dict) -> Dict:
        """
        Reissue/Exchange a ticket
        
        Args:
            reissue_params: Dict containing:
                - ticket_number: str
                - universal_record_locator: str (PNR)
                - new_segments: List[Dict] with new flight details
                - additional_collection: float (if fare difference)
        """
        payload = {
            "targetBranch": self.target_branch,
            "universalRecordLocatorCode": reissue_params['universal_record_locator'],
            "ticketNumber": reissue_params['ticket_number'],
            "airExchangeModifiers": {
                "exchangeType": "Reissue"
            }
        }
        
        if reissue_params.get('new_segments'):
            payload['airSegment'] = reissue_params['new_segments']
        
        if reissue_params.get('additional_collection'):
            payload['additionalCollection'] = {
                "amount": reissue_params['additional_collection'],
                "currency": reissue_params.get('currency', 'USD')
            }
        
        return self._make_request('AirExchangeReq', payload)

    def retrieve_pnr(self, pnr: str) -> Dict:
        """
        Retrieve booking details by PNR
        
        Args:
            pnr: Passenger Name Record number
        """
        payload = {
            "targetBranch": self.target_branch,
            "universalRecordLocatorCode": pnr
        }
        return self._make_request('UniversalRecordRetrieveReq', payload)

    def get_fare_rules(self, fare_params: Dict) -> Dict:
        """
        Get fare rules for a specific fare
        
        Args:
            fare_params: Dict containing fare basis and other details
        """
        payload = {
            "targetBranch": self.target_branch,
            "fareBasis": fare_params['fare_basis'],
            "origin": fare_params['origin'],
            "destination": fare_params['destination'],
            "carrier": fare_params.get('carrier', '')
        }
        return self._make_request('AirFareRulesReq', payload)

    def _build_search_payload(self, params: Dict) -> Dict:
        """Build payload for flight search"""
        passengers = params.get('passengers', {'adult': 1})

        payload = {
            "targetBranch": self.target_branch,
            "billingPointOfSaleInfo": {
                "origin": "US"
            },
            "searchPassenger": [
                {
                    "code": "ADT",
                    "quantity": passengers.get('adult', 1)
                }
            ],
            "searchAirLeg": []
        }

        # Add child passengers
        if passengers.get('child', 0) > 0:
            payload["searchPassenger"].append({
                "code": "CNN",
                "quantity": passengers['child']
            })

        # Add infant passengers
        if passengers.get('infant', 0) > 0:
            payload["searchPassenger"].append({
                "code": "INF",
                "quantity": passengers['infant']
            })

        # Build air legs
        air_leg = {
            "searchOrigin": [{
                "airport": {
                    "code": params['origin']
                }
            }],
            "searchDestination": [{
                "airport": {
                    "code": params['destination']
                }
            }],
            "searchDepartureTime": [{
                "date": params['departure_date']
            }]
        }

        # Add cabin class preference
        if params.get('cabin_class'):
            cabin_map = {
                'Economy': 'Y',
                'PremiumEconomy': 'W',
                'Business': 'C',
                'First': 'F'
            }
            air_leg["airLegModifiers"] = {
                "preferredCabins": [{
                    "cabinClass": cabin_map.get(params['cabin_class'], 'Y')
                }]
            }

        payload["searchAirLeg"].append(air_leg)

        # Add return leg if specified
        if params.get('return_date'):
            return_leg = {
                "searchOrigin": [{
                    "airport": {
                        "code": params['destination']
                    }
                }],
                "searchDestination": [{
                    "airport": {
                        "code": params['origin']
                    }
                }],
                "searchDepartureTime": [{
                    "date": params['return_date']
                }]
            }
            payload["searchAirLeg"].append(return_leg)

        return payload

    def _build_availability_payload(self, params: Dict) -> Dict:
        """Build payload for availability check"""
        return {
            "targetBranch": self.target_branch,
            "billingPointOfSaleInfo": {
                "origin": "US"
            },
            "searchAirLeg": [{
                "searchOrigin": [{
                    "airport": {"code": params['origin']}
                }],
                "searchDestination": [{
                    "airport": {"code": params['destination']}
                }],
                "searchDepartureTime": [{
                    "date": params['departure_date']
                }]
            }]
        }

    def _build_booking_payload(self, params: Dict) -> Dict:
        """
        Build payload for booking creation
        
        params should contain:
        - pricing_solution_key: str (from search results)
        - passengers: List[Dict] with passenger details
        - contact_info: Dict with email, phone
        """
        payload = {
            "targetBranch": self.target_branch,
            "billingPointOfSaleInfo": {
                "origin": "US"
            },
            "airPricingSolution": {
                "key": params['pricing_solution_key']
            },
            "bookingTraveler": []
        }
        
        # Add passengers
        for idx, passenger in enumerate(params.get('passengers', [])):
            traveler = {
                "key": f"Traveler_{idx}",
                "travelerType": passenger.get('type', 'ADT'),
                "bookingTravelerName": {
                    "prefix": passenger.get('title', 'Mr'),
                    "first": passenger['first_name'],
                    "last": passenger['last_name']
                },
                "dob": passenger.get('date_of_birth'),
                "gender": passenger.get('gender', 'M'),
                "phoneNumber": [{
                    "type": "Mobile",
                    "number": params.get('contact_info', {}).get('phone', '')
                }],
                "email": [{
                    "type": "Primary",
                    "emailID": params.get('contact_info', {}).get('email', '')
                }]
            }
            
            # Add passport info if international
            if passenger.get('passport_number'):
                traveler['document'] = {
                    "type": "Passport",
                    "number": passenger['passport_number'],
                    "expiryDate": passenger.get('passport_expiry'),
                    "issuingCountry": passenger.get('passport_country')
                }
            
            payload["bookingTraveler"].append(traveler)
        
        return payload

    def _build_cancel_payload(self, pnr: str) -> Dict:
        """Build payload for booking cancellation"""
        return {
            "targetBranch": self.target_branch,
            "universalRecordLocatorCode": pnr
        }

    def _build_ticket_payload(self, params: Dict) -> Dict:
        """
        Build payload for ticket issuance
        
        params should contain:
        - universal_record_locator: str (PNR)
        - air_reservation_locator: str
        - payment_info: Dict with payment details
        """
        return {
            "targetBranch": self.target_branch,
            "universalRecordLocatorCode": params['universal_record_locator'],
            "airReservationLocatorCode": params.get('air_reservation_locator'),
            "ticketingModifiers": {
                "ticketingType": "Ticketing",
                "platingCarrier": params.get('plating_carrier', 'XX')
            },
            "formOfPayment": {
                "type": params.get('payment_info', {}).get('type', 'Cash'),
                "creditCard": params.get('payment_info', {}).get('card_details')
            }
        }

    def parse_search_results(self, response: Dict) -> List[Dict]:
        """
        Parse Galileo search response into standardized format

        Returns:
            List of flight options with pricing and details
        """
        flights = []

        try:
            if 'airPricingSolution' in response:
                for solution in response['airPricingSolution']:
                    flight_data = self._extract_flight_data(solution)
                    if flight_data:
                        flights.append(flight_data)
        except Exception as e:
            logger.error(f"Error parsing search results: {str(e)}")

        return flights

    def _extract_flight_data(self, solution: Dict) -> Optional[Dict]:
        """Extract flight information from pricing solution"""
        try:
            # Implementation to parse Galileo response format
            # This would depend on the exact API response structure
            return {
                'price': solution.get('totalPrice', '0'),
                'currency': solution.get('currency', 'USD'),
                'segments': [],  # Flight segments
                'airline': '',   # Main airline
                'booking_class': '',
                'fare_basis': ''
            }
        except Exception as e:
            logger.error(f"Error extracting flight data: {str(e)}")
            return None


# Singleton instance
galileo_client = GalileoAPIClient()