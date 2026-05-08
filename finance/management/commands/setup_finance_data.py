from django.core.management.base import BaseCommand
from finance.models import Airline, PaymentMethod


class Command(BaseCommand):
    help = 'Setup finance app data - airlines and payment methods'

    def handle(self, *args, **options):
        # Create airlines
        airlines_data = [
            ('SA', 'Saudia', 'Saudi Arabia'),
            ('SV', 'Saudia Cargo', 'Saudi Arabia'),
            ('F3', 'Flyadeal', 'Saudi Arabia'),
            ('XY', 'Flynas', 'Saudi Arabia'),
            ('EK', 'Emirates', 'UAE'),
            ('EY', 'Etihad Airways', 'UAE'),
            ('QR', 'Qatar Airways', 'Qatar'),
            ('GF', 'Gulf Air', 'Bahrain'),
            ('KU', 'Kuwait Airways', 'Kuwait'),
            ('WY', 'Oman Air', 'Oman'),
            ('IR', 'Iran Air', 'Iran'),
            ('TK', 'Turkish Airlines', 'Turkey'),
            ('BA', 'British Airways', 'UK'),
            ('AF', 'Air France', 'France'),
            ('LH', 'Lufthansa', 'Germany'),
            ('SQ', 'Singapore Airlines', 'Singapore'),
            ('CX', 'Cathay Pacific', 'Hong Kong'),
            ('MH', 'Malaysia Airlines', 'Malaysia'),
            ('TG', 'Thai Airways', 'Thailand'),
            ('AI', 'Air India', 'India'),
            ('PK', 'Pakistan International Airlines', 'Pakistan'),
        ]

        created_airlines = 0
        for code, name, country in airlines_data:
            airline, created = Airline.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'country': country,
                    'is_active': True
                }
            )
            if created:
                created_airlines += 1
                self.stdout.write(f'Created airline: {airline}')
            else:
                self.stdout.write(f'Airline already exists: {airline}')

        # Create payment methods
        payment_methods_data = [
            ('bkash', 'bKash - Mobile Financial Service'),
            ('span', 'SPAN - Saudi Payments Network'),
            ('cash', 'Cash Payment'),
            ('card', 'Credit/Debit Card'),
            ('bank', 'Bank Transfer'),
            ('nagad', 'Nagad - Mobile Financial Service'),
            ('other', 'Other Payment Methods'),
        ]

        created_payment_methods = 0
        for method_name, description in payment_methods_data:
            payment_method, created = PaymentMethod.objects.get_or_create(
                name=method_name,
                defaults={
                    'description': description,
                    'is_active': True
                }
            )
            if created:
                created_payment_methods += 1
                self.stdout.write(f'Created payment method: {payment_method.get_name_display()}')
            else:
                self.stdout.write(f'Payment method already exists: {payment_method.get_name_display()}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_airlines} airlines and {created_payment_methods} payment methods'
            )
        )
