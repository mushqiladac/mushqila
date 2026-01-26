# accounts/management/commands/delete_demo_data.py
"""
Management command to delete all demo/test data
Run: python manage.py delete_demo_data
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Delete all demo/test data from the system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion without prompting',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write(self.style.WARNING('DELETE DEMO DATA'))
        self.stdout.write(self.style.WARNING('=' * 80))
        
        # Count items to delete
        demo_agent = User.objects.filter(email='demo.agent@mushqila.com').first()
        
        if not demo_agent:
            self.stdout.write(self.style.SUCCESS('\n✓ No demo data found. Database is clean.'))
            return
        
        # Count related data
        from accounts.models.transaction_tracking import (
            TransactionLog, AgentLedger, DailyTransactionSummary, 
            MonthlyAgentReport, TransactionAuditLog
        )
        from accounts.models.accounting import JournalEntry
        from flights.models.booking_models import Booking, Passenger, PNR, Ticket, Payment
        from flights.models.flight_models import FlightSearch, FlightItinerary
        
        counts = {
            'agent': 1 if demo_agent else 0,
            'transaction_logs': TransactionLog.objects.filter(agent=demo_agent).count(),
            'ledger_entries': AgentLedger.objects.filter(agent=demo_agent).count(),
            'daily_summaries': DailyTransactionSummary.objects.filter(agent=demo_agent).count(),
            'monthly_reports': MonthlyAgentReport.objects.filter(agent=demo_agent).count(),
            'audit_logs': TransactionAuditLog.objects.filter(
                transaction_log__agent=demo_agent
            ).count(),
            'journal_entries': JournalEntry.objects.filter(user=demo_agent).count(),
            'bookings': Booking.objects.filter(agent=demo_agent).count(),
            'passengers': Passenger.objects.filter(passport_number='A12345678').count(),
            'searches': FlightSearch.objects.filter(user=demo_agent).count(),
        }
        
        total_items = sum(counts.values())
        
        if total_items == 0:
            self.stdout.write(self.style.SUCCESS('\n✓ No demo data found. Database is clean.'))
            return
        
        # Display what will be deleted
        self.stdout.write('\n' + self.style.WARNING('The following demo data will be DELETED:'))
        self.stdout.write('')
        for key, count in counts.items():
            if count > 0:
                self.stdout.write(f'  • {key.replace("_", " ").title()}: {count}')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING(f'Total items to delete: {total_items}'))
        self.stdout.write('')
        
        # Confirm deletion
        if not options['confirm']:
            confirm = input(self.style.ERROR('Are you sure you want to DELETE all demo data? (yes/no): '))
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.SUCCESS('\nDeletion cancelled.'))
                return
        
        # Delete data
        self.stdout.write('\n' + self.style.WARNING('Deleting demo data...'))
        
        deleted_counts = {}
        
        with transaction.atomic():
            # Delete in correct order (respecting foreign keys)
            
            # 1. Audit logs
            count = TransactionAuditLog.objects.filter(
                transaction_log__agent=demo_agent
            ).delete()[0]
            if count > 0:
                deleted_counts['Audit Logs'] = count
                self.stdout.write(f'  ✓ Deleted {count} audit logs')
            
            # 2. Journal entries
            count = JournalEntry.objects.filter(user=demo_agent).delete()[0]
            if count > 0:
                deleted_counts['Journal Entries'] = count
                self.stdout.write(f'  ✓ Deleted {count} journal entries')
            
            # 3. Daily summaries
            count = DailyTransactionSummary.objects.filter(agent=demo_agent).delete()[0]
            if count > 0:
                deleted_counts['Daily Summaries'] = count
                self.stdout.write(f'  ✓ Deleted {count} daily summaries')
            
            # 4. Monthly reports
            count = MonthlyAgentReport.objects.filter(agent=demo_agent).delete()[0]
            if count > 0:
                deleted_counts['Monthly Reports'] = count
                self.stdout.write(f'  ✓ Deleted {count} monthly reports')
            
            # 5. Agent ledger
            count = AgentLedger.objects.filter(agent=demo_agent).delete()[0]
            if count > 0:
                deleted_counts['Ledger Entries'] = count
                self.stdout.write(f'  ✓ Deleted {count} ledger entries')
            
            # 6. Transaction logs
            count = TransactionLog.objects.filter(agent=demo_agent).delete()[0]
            if count > 0:
                deleted_counts['Transaction Logs'] = count
                self.stdout.write(f'  ✓ Deleted {count} transaction logs')
            
            # 7. Tickets (if any)
            tickets_deleted = 0
            bookings = Booking.objects.filter(agent=demo_agent)
            for booking in bookings:
                tickets_deleted += Ticket.objects.filter(
                    booking_passenger__booking=booking
                ).delete()[0]
            if tickets_deleted > 0:
                deleted_counts['Tickets'] = tickets_deleted
                self.stdout.write(f'  ✓ Deleted {tickets_deleted} tickets')
            
            # 8. Payments
            payments_deleted = 0
            for booking in bookings:
                payments_deleted += Payment.objects.filter(booking=booking).delete()[0]
            if payments_deleted > 0:
                deleted_counts['Payments'] = payments_deleted
                self.stdout.write(f'  ✓ Deleted {payments_deleted} payments')
            
            # 9. PNRs
            pnrs_deleted = 0
            for booking in bookings:
                pnrs_deleted += PNR.objects.filter(booking=booking).delete()[0]
            if pnrs_deleted > 0:
                deleted_counts['PNRs'] = pnrs_deleted
                self.stdout.write(f'  ✓ Deleted {pnrs_deleted} PNRs')
            
            # 10. Bookings
            count = bookings.delete()[0]
            if count > 0:
                deleted_counts['Bookings'] = count
                self.stdout.write(f'  ✓ Deleted {count} bookings')
            
            # 11. Flight itineraries (created by demo agent)
            itineraries = FlightItinerary.objects.filter(search__user=demo_agent)
            count = itineraries.delete()[0]
            if count > 0:
                deleted_counts['Flight Itineraries'] = count
                self.stdout.write(f'  ✓ Deleted {count} flight itineraries')
            
            # 12. Flight searches
            count = FlightSearch.objects.filter(user=demo_agent).delete()[0]
            if count > 0:
                deleted_counts['Flight Searches'] = count
                self.stdout.write(f'  ✓ Deleted {count} flight searches')
            
            # 13. Demo passenger
            count = Passenger.objects.filter(passport_number='A12345678').delete()[0]
            if count > 0:
                deleted_counts['Passengers'] = count
                self.stdout.write(f'  ✓ Deleted {count} passengers')
            
            # 14. Demo agent (last)
            if demo_agent:
                demo_agent.delete()
                deleted_counts['Demo Agent'] = 1
                self.stdout.write(f'  ✓ Deleted demo agent')
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('DEMO DATA DELETED SUCCESSFULLY'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')
        self.stdout.write('Summary:')
        for key, count in deleted_counts.items():
            self.stdout.write(f'  ✓ {key}: {count} deleted')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Total items deleted: {sum(deleted_counts.values())}'))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Database is now clean and ready for production data!'))
        self.stdout.write('')
