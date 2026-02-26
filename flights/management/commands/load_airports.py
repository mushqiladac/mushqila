from django.core.management.base import BaseCommand
from flights.models import Airport

class Command(BaseCommand):
    help = 'Load sample airport data'

    def handle(self, *args, **kwargs):
        airports_data = [
            # Bangladesh
            {'iata_code': 'DAC', 'icao_code': 'VGHS', 'name': 'Hazrat Shahjalal International Airport', 'city': 'Dhaka', 'country': 'Bangladesh', 'country_code': 'BD', 'timezone': 'Asia/Dhaka', 'latitude': 23.843347, 'longitude': 90.397783},
            {'iata_code': 'CXB', 'icao_code': 'VGCB', 'name': "Cox's Bazar Airport", 'city': "Cox's Bazar", 'country': 'Bangladesh', 'country_code': 'BD', 'timezone': 'Asia/Dhaka', 'latitude': 21.452194, 'longitude': 91.963889},
            {'iata_code': 'CGP', 'icao_code': 'VGEG', 'name': 'Shah Amanat International Airport', 'city': 'Chittagong', 'country': 'Bangladesh', 'country_code': 'BD', 'timezone': 'Asia/Dhaka', 'latitude': 22.249611, 'longitude': 91.813286},
            {'iata_code': 'ZYL', 'icao_code': 'VGSY', 'name': 'Osmani International Airport', 'city': 'Sylhet', 'country': 'Bangladesh', 'country_code': 'BD', 'timezone': 'Asia/Dhaka', 'latitude': 24.963242, 'longitude': 91.866783},
            {'iata_code': 'JSR', 'icao_code': 'VGJR', 'name': 'Jessore Airport', 'city': 'Jessore', 'country': 'Bangladesh', 'country_code': 'BD', 'timezone': 'Asia/Dhaka', 'latitude': 23.183778, 'longitude': 89.160833},
            
            # Saudi Arabia
            {'iata_code': 'JED', 'icao_code': 'OEJN', 'name': 'King Abdulaziz International Airport', 'city': 'Jeddah', 'country': 'Saudi Arabia', 'country_code': 'SA', 'timezone': 'Asia/Riyadh', 'latitude': 21.679564, 'longitude': 39.156536},
            {'iata_code': 'RUH', 'icao_code': 'OERK', 'name': 'King Khalid International Airport', 'city': 'Riyadh', 'country': 'Saudi Arabia', 'country_code': 'SA', 'timezone': 'Asia/Riyadh', 'latitude': 24.957639, 'longitude': 46.698776},
            {'iata_code': 'MED', 'icao_code': 'OEMA', 'name': 'Prince Mohammad bin Abdulaziz Airport', 'city': 'Madinah', 'country': 'Saudi Arabia', 'country_code': 'SA', 'timezone': 'Asia/Riyadh', 'latitude': 24.553422, 'longitude': 39.705061},
            {'iata_code': 'DMM', 'icao_code': 'OEDF', 'name': 'King Fahd International Airport', 'city': 'Dammam', 'country': 'Saudi Arabia', 'country_code': 'SA', 'timezone': 'Asia/Riyadh', 'latitude': 26.471161, 'longitude': 49.797931},
            
            # UAE
            {'iata_code': 'DXB', 'icao_code': 'OMDB', 'name': 'Dubai International Airport', 'city': 'Dubai', 'country': 'UAE', 'country_code': 'AE', 'timezone': 'Asia/Dubai', 'latitude': 25.252778, 'longitude': 55.364444},
            {'iata_code': 'AUH', 'icao_code': 'OMAA', 'name': 'Abu Dhabi International Airport', 'city': 'Abu Dhabi', 'country': 'UAE', 'country_code': 'AE', 'timezone': 'Asia/Dubai', 'latitude': 24.433056, 'longitude': 54.651111},
            {'iata_code': 'SHJ', 'icao_code': 'OMSJ', 'name': 'Sharjah International Airport', 'city': 'Sharjah', 'country': 'UAE', 'country_code': 'AE', 'timezone': 'Asia/Dubai', 'latitude': 25.328575, 'longitude': 55.517222},
            
            # India
            {'iata_code': 'DEL', 'icao_code': 'VIDP', 'name': 'Indira Gandhi International Airport', 'city': 'New Delhi', 'country': 'India', 'country_code': 'IN', 'timezone': 'Asia/Kolkata', 'latitude': 28.556161, 'longitude': 77.100444},
            {'iata_code': 'BOM', 'icao_code': 'VABB', 'name': 'Chhatrapati Shivaji International Airport', 'city': 'Mumbai', 'country': 'India', 'country_code': 'IN', 'timezone': 'Asia/Kolkata', 'latitude': 19.088686, 'longitude': 72.867919},
            {'iata_code': 'CCU', 'icao_code': 'VECC', 'name': 'Netaji Subhas Chandra Bose International Airport', 'city': 'Kolkata', 'country': 'India', 'country_code': 'IN', 'timezone': 'Asia/Kolkata', 'latitude': 22.654739, 'longitude': 88.446722},
            
            # Malaysia
            {'iata_code': 'KUL', 'icao_code': 'WMKK', 'name': 'Kuala Lumpur International Airport', 'city': 'Kuala Lumpur', 'country': 'Malaysia', 'country_code': 'MY', 'timezone': 'Asia/Kuala_Lumpur', 'latitude': 2.745578, 'longitude': 101.709917},
            
            # Singapore
            {'iata_code': 'SIN', 'icao_code': 'WSSS', 'name': 'Singapore Changi Airport', 'city': 'Singapore', 'country': 'Singapore', 'country_code': 'SG', 'timezone': 'Asia/Singapore', 'latitude': 1.350189, 'longitude': 103.994433},
            
            # Thailand
            {'iata_code': 'BKK', 'icao_code': 'VTBS', 'name': 'Suvarnabhumi Airport', 'city': 'Bangkok', 'country': 'Thailand', 'country_code': 'TH', 'timezone': 'Asia/Bangkok', 'latitude': 13.681108, 'longitude': 100.747283},
            
            # UK
            {'iata_code': 'LHR', 'icao_code': 'EGLL', 'name': 'London Heathrow Airport', 'city': 'London', 'country': 'United Kingdom', 'country_code': 'GB', 'timezone': 'Europe/London', 'latitude': 51.469603, 'longitude': -0.453566},
            
            # USA
            {'iata_code': 'JFK', 'icao_code': 'KJFK', 'name': 'John F. Kennedy International Airport', 'city': 'New York', 'country': 'USA', 'country_code': 'US', 'timezone': 'America/New_York', 'latitude': 40.639751, 'longitude': -73.778925},
        ]
        
        created_count = 0
        updated_count = 0
        
        for airport_data in airports_data:
            airport, created = Airport.objects.update_or_create(
                iata_code=airport_data['iata_code'],
                defaults=airport_data
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded {created_count} new airports and updated {updated_count} existing airports'
            )
        )
