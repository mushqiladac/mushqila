# accounts/services/automated_reporting_service.py
"""
Automated Reporting Service
Generates comprehensive reports for staff to provide to agents
"""

from django.db.models import Sum, Count, Q, F, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class AutomatedReportingService:
    """
    Service for generating automated reports
    Staff can use these to provide reports to agents at any time
    """
    
    def generate_agent_daily_report(self, agent, date=None):
        """
        Generate comprehensive daily report for an agent
        """
        try:
            from accounts.models.transaction_tracking import (
                TransactionLog, DailyTransactionSummary, AgentLedger
            )
            
            if date is None:
                date = timezone.now().date()
            
            # Get or create daily summary
            summary, created = DailyTransactionSummary.objects.get_or_create(
                agent=agent,
                summary_date=date
            )
            
            # Get all transactions for the day
            transactions = TransactionLog.objects.filter(
                agent=agent,
                transaction_date__date=date,
                status='completed'
            ).select_related('booking', 'ticket', 'payment')
            
            # Calculate statistics
            stats = {
                'date': date.strftime('%Y-%m-%d'),
                'agent_name': agent.get_full_name(),
                'agent_code': agent.agent_code if hasattr(agent, 'agent_code') else '',
                
                # Transaction counts
                'total_transactions': transactions.count(),
                'tickets_issued': transactions.filter(transaction_type='ticket_issue').count(),
                'tickets_voided': transactions.filter(transaction_type='ticket_void').count(),
                'tickets_cancelled': transactions.filter(transaction_type='ticket_cancel').count(),
                'tickets_refunded': transactions.filter(transaction_type='ticket_refund').count(),
                'tickets_reissued': transactions.filter(transaction_type='ticket_reissue').count(),
                
                # Financial summary
                'total_sales': transactions.filter(
                    transaction_type='ticket_issue'
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
                
                'total_refunds': transactions.filter(
                    transaction_type='ticket_refund'
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
                
                'total_commissions': transactions.filter(
                    transaction_type__in=['commission_earned', 'commission_paid']
                ).aggregate(total=Sum('commission_amount'))['total'] or Decimal('0.00'),
                
                'payments_received': transactions.filter(
                    transaction_type='payment_received'
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
            }
            
            # Calculate net revenue
            stats['net_revenue'] = stats['total_sales'] - stats['total_refunds']
            
            # Get ledger balance
            last_ledger = AgentLedger.objects.filter(
                agent=agent,
                entry_date__lte=date
            ).order_by('-entry_date', '-created_at').first()
            
            stats['closing_balance'] = last_ledger.balance_after if last_ledger else Decimal('0.00')
            
            # Transaction details
            stats['transactions'] = []
            for trans in transactions:
                stats['transactions'].append({
                    'transaction_number': trans.transaction_number,
                    'type': trans.get_transaction_type_display(),
                    'time': trans.transaction_date.strftime('%H:%M:%S'),
                    'amount': str(trans.total_amount),
                    'currency': trans.currency,
                    'status': trans.get_status_display(),
                    'description': trans.description,
                    'ticket_number': trans.ticket.ticket_number if trans.ticket else '',
                    'booking_reference': trans.booking.booking_reference if trans.booking else ''
                })
            
            return {
                'success': True,
                'report': stats,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating daily report: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def generate_agent_monthly_report(self, agent, year, month):
        """
        Generate comprehensive monthly report for an agent
        """
        try:
            from accounts.models.transaction_tracking import (
                TransactionLog, MonthlyAgentReport
            )
            from calendar import monthrange
            
            # Get period dates
            period_start = datetime(year, month, 1).date()
            last_day = monthrange(year, month)[1]
            period_end = datetime(year, month, last_day).date()
            
            # Get all transactions for the month
            transactions = TransactionLog.objects.filter(
                agent=agent,
                transaction_date__date__gte=period_start,
                transaction_date__date__lte=period_end,
                status='completed'
            )
            
            # Calculate statistics
            stats = {
                'agent_name': agent.get_full_name(),
                'agent_code': agent.agent_code if hasattr(agent, 'agent_code') else '',
                'period': f"{year}-{month:02d}",
                'period_start': period_start.strftime('%Y-%m-%d'),
                'period_end': period_end.strftime('%Y-%m-%d'),
                
                # Transaction counts
                'total_transactions': transactions.count(),
                'tickets_issued': transactions.filter(transaction_type='ticket_issue').count(),
                'tickets_voided': transactions.filter(transaction_type='ticket_void').count(),
                'tickets_cancelled': transactions.filter(transaction_type='ticket_cancel').count(),
                'tickets_refunded': transactions.filter(transaction_type='ticket_refund').count(),
                'tickets_reissued': transactions.filter(transaction_type='ticket_reissue').count(),
                
                # Financial summary
                'gross_sales': transactions.filter(
                    transaction_type='ticket_issue'
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
                
                'total_refunds': transactions.filter(
                    transaction_type='ticket_refund'
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
                
                'commission_earned': transactions.filter(
                    transaction_type='commission_earned'
                ).aggregate(total=Sum('commission_amount'))['total'] or Decimal('0.00'),
                
                'commission_paid': transactions.filter(
                    transaction_type='commission_paid'
                ).aggregate(total=Sum('commission_amount'))['total'] or Decimal('0.00'),
                
                'payments_received': transactions.filter(
                    transaction_type='payment_received'
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'),
            }
            
            # Calculate derived values
            stats['net_sales'] = stats['gross_sales'] - stats['total_refunds']
            stats['net_commission'] = stats['commission_earned'] - stats['commission_paid']
            
            # Average transaction value
            if stats['tickets_issued'] > 0:
                stats['average_ticket_value'] = stats['gross_sales'] / stats['tickets_issued']
            else:
                stats['average_ticket_value'] = Decimal('0.00')
            
            # Daily breakdown
            stats['daily_breakdown'] = []
            current_date = period_start
            while current_date <= period_end:
                day_trans = transactions.filter(transaction_date__date=current_date)
                stats['daily_breakdown'].append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'transactions': day_trans.count(),
                    'sales': str(day_trans.filter(
                        transaction_type='ticket_issue'
                    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')),
                    'refunds': str(day_trans.filter(
                        transaction_type='ticket_refund'
                    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00'))
                })
                current_date += timedelta(days=1)
            
            # Top routes
            stats['top_routes'] = self._get_top_routes(agent, period_start, period_end)
            
            # Top airlines
            stats['top_airlines'] = self._get_top_airlines(agent, period_start, period_end)
            
            return {
                'success': True,
                'report': stats,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating monthly report: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def generate_all_agents_summary(self, date=None):
        """
        Generate summary report for all agents (for staff/admin)
        """
        try:
            from accounts.models.transaction_tracking import TransactionLog
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            
            if date is None:
                date = timezone.now().date()
            
            # Get all agents
            agents = User.objects.filter(
                user_type__in=['agent', 'super_agent'],
                is_active=True
            )
            
            summary = {
                'date': date.strftime('%Y-%m-%d'),
                'total_agents': agents.count(),
                'agents': []
            }
            
            for agent in agents:
                # Get agent's transactions for the day
                transactions = TransactionLog.objects.filter(
                    agent=agent,
                    transaction_date__date=date,
                    status='completed'
                )
                
                agent_data = {
                    'agent_name': agent.get_full_name(),
                    'agent_code': agent.agent_code if hasattr(agent, 'agent_code') else '',
                    'email': agent.email,
                    'total_transactions': transactions.count(),
                    'tickets_issued': transactions.filter(transaction_type='ticket_issue').count(),
                    'total_sales': str(transactions.filter(
                        transaction_type='ticket_issue'
                    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')),
                    'total_refunds': str(transactions.filter(
                        transaction_type='ticket_refund'
                    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')),
                    'commissions': str(transactions.filter(
                        transaction_type='commission_earned'
                    ).aggregate(total=Sum('commission_amount'))['total'] or Decimal('0.00'))
                }
                
                summary['agents'].append(agent_data)
            
            # Calculate totals
            summary['totals'] = {
                'total_transactions': sum(a['total_transactions'] for a in summary['agents']),
                'total_tickets': sum(a['tickets_issued'] for a in summary['agents']),
                'total_sales': str(sum(Decimal(a['total_sales']) for a in summary['agents'])),
                'total_refunds': str(sum(Decimal(a['total_refunds']) for a in summary['agents'])),
                'total_commissions': str(sum(Decimal(a['commissions']) for a in summary['agents']))
            }
            
            return {
                'success': True,
                'report': summary,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating all agents summary: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def generate_financial_statement(self, start_date, end_date):
        """
        Generate financial statement for a period
        """
        try:
            from accounts.models.accounting import Account, JournalEntry
            
            statement = {
                'period_start': start_date.strftime('%Y-%m-%d'),
                'period_end': end_date.strftime('%Y-%m-%d'),
                'assets': {},
                'liabilities': {},
                'equity': {},
                'revenue': {},
                'expenses': {}
            }
            
            # Get all accounts
            accounts = Account.objects.filter(is_active=True)
            
            for account in accounts:
                balance = account.get_balance(as_of_date=end_date)
                
                account_data = {
                    'code': account.code,
                    'name': account.name,
                    'balance': str(balance)
                }
                
                if account.account_type == 'asset':
                    statement['assets'][account.code] = account_data
                elif account.account_type == 'liability':
                    statement['liabilities'][account.code] = account_data
                elif account.account_type == 'equity':
                    statement['equity'][account.code] = account_data
                elif account.account_type == 'revenue':
                    statement['revenue'][account.code] = account_data
                elif account.account_type == 'expense':
                    statement['expenses'][account.code] = account_data
            
            # Calculate totals
            statement['total_assets'] = str(sum(
                Decimal(a['balance']) for a in statement['assets'].values()
            ))
            statement['total_liabilities'] = str(sum(
                Decimal(l['balance']) for l in statement['liabilities'].values()
            ))
            statement['total_equity'] = str(sum(
                Decimal(e['balance']) for e in statement['equity'].values()
            ))
            statement['total_revenue'] = str(sum(
                Decimal(r['balance']) for r in statement['revenue'].values()
            ))
            statement['total_expenses'] = str(sum(
                Decimal(e['balance']) for e in statement['expenses'].values()
            ))
            
            # Calculate net income
            statement['net_income'] = str(
                Decimal(statement['total_revenue']) - Decimal(statement['total_expenses'])
            )
            
            return {
                'success': True,
                'statement': statement,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating financial statement: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _get_top_routes(self, agent, start_date, end_date, limit=10):
        """Get top routes for an agent"""
        try:
            from flights.models import Booking
            
            bookings = Booking.objects.filter(
                agent=agent,
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
                status__in=['confirmed', 'ticketed']
            ).select_related('itinerary')
            
            routes = {}
            for booking in bookings:
                if booking.itinerary:
                    route = f"{booking.itinerary.origin} - {booking.itinerary.destination}"
                    if route in routes:
                        routes[route]['count'] += 1
                        routes[route]['revenue'] += booking.total_amount
                    else:
                        routes[route] = {
                            'route': route,
                            'count': 1,
                            'revenue': booking.total_amount
                        }
            
            # Sort by count
            sorted_routes = sorted(routes.values(), key=lambda x: x['count'], reverse=True)[:limit]
            
            return [
                {
                    'route': r['route'],
                    'bookings': r['count'],
                    'revenue': str(r['revenue'])
                }
                for r in sorted_routes
            ]
            
        except Exception as e:
            logger.error(f"Error getting top routes: {str(e)}", exc_info=True)
            return []
    
    def _get_top_airlines(self, agent, start_date, end_date, limit=10):
        """Get top airlines for an agent"""
        try:
            from flights.models import Ticket
            
            tickets = Ticket.objects.filter(
                booking__agent=agent,
                issued_at__date__gte=start_date,
                issued_at__date__lte=end_date,
                status='issued'
            ).values('airline__name', 'airline__code').annotate(
                ticket_count=Count('id'),
                total_revenue=Sum('total_amount')
            ).order_by('-ticket_count')[:limit]
            
            return [
                {
                    'airline': f"{t['airline__name']} ({t['airline__code']})",
                    'tickets': t['ticket_count'],
                    'revenue': str(t['total_revenue'])
                }
                for t in tickets
            ]
            
        except Exception as e:
            logger.error(f"Error getting top airlines: {str(e)}", exc_info=True)
            return []
