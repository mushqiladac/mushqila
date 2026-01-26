# accounts/services/agent_balance_service.py
"""
Real-time Agent Balance and Outstanding Tracking Service
Automatically tracks agent balance, outstanding amounts, and credit limits
"""

from django.db import transaction
from django.db.models import Sum, Q, F
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class AgentBalanceService:
    """
    Service for managing agent balances and outstanding amounts
    Real-time updates on every transaction
    """
    
    def get_agent_balance(self, agent):
        """
        Get current balance for an agent
        Returns: {
            'current_balance': Decimal,
            'outstanding_amount': Decimal,
            'credit_limit': Decimal,
            'available_credit': Decimal,
            'total_sales': Decimal,
            'total_payments': Decimal,
            'total_refunds': Decimal,
            'last_payment_date': datetime,
            'last_transaction_date': datetime
        }
        """
        try:
            from accounts.models.transaction_tracking import AgentLedger, TransactionLog
            
            # Get latest ledger entry for current balance
            latest_ledger = AgentLedger.objects.filter(
                agent=agent
            ).order_by('-entry_date', '-created_at').first()
            
            current_balance = latest_ledger.balance_after if latest_ledger else Decimal('0.00')
            
            # Calculate outstanding (unpaid tickets) from TransactionLog
            outstanding_tickets = TransactionLog.objects.filter(
                agent=agent,
                transaction_type='ticket_issue',
                status='completed',
                accounting_posted=True
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            # Subtract payments received
            payments_received = TransactionLog.objects.filter(
                agent=agent,
                transaction_type='payment_received',
                status='completed'
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            outstanding_amount = outstanding_tickets - payments_received
            if outstanding_amount < 0:
                outstanding_amount = Decimal('0.00')
            
            # Get credit limit
            credit_limit = agent.credit_limit if hasattr(agent, 'credit_limit') else Decimal('0.00')
            
            # Calculate available credit
            available_credit = credit_limit - outstanding_amount
            
            # Get total sales (all time)
            total_sales = TransactionLog.objects.filter(
                agent=agent,
                transaction_type='ticket_issue',
                status='completed'
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            # Get total payments received
            total_payments = TransactionLog.objects.filter(
                agent=agent,
                transaction_type='payment_received',
                status='completed'
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            # Get total refunds
            total_refunds = TransactionLog.objects.filter(
                agent=agent,
                transaction_type='ticket_refund',
                status='completed'
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            # Get last payment date
            last_payment = TransactionLog.objects.filter(
                agent=agent,
                transaction_type='payment_received',
                status='completed'
            ).order_by('-transaction_date').first()
            
            # Get last transaction date
            last_transaction = TransactionLog.objects.filter(
                agent=agent,
                status='completed'
            ).order_by('-transaction_date').first()
            
            return {
                'success': True,
                'agent_name': agent.get_full_name(),
                'agent_code': agent.username if hasattr(agent, 'username') else '',
                'current_balance': current_balance,
                'outstanding_amount': outstanding_amount,
                'credit_limit': credit_limit,
                'available_credit': available_credit,
                'total_sales': total_sales,
                'total_payments': total_payments,
                'total_refunds': total_refunds,
                'net_sales': total_sales - total_refunds,
                'last_payment_date': last_payment.transaction_date if last_payment else None,
                'last_transaction_date': last_transaction.transaction_date if last_transaction else None,
                'updated_at': timezone.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting agent balance: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def get_outstanding_details(self, agent):
        """
        Get detailed breakdown of outstanding amounts
        """
        try:
            from accounts.models.transaction_tracking import TransactionLog
            from flights.models import Ticket, Payment
            
            # Get all unpaid tickets
            unpaid_tickets = Ticket.objects.filter(
                booking__agent=agent,
                status='issued'
            ).exclude(
                booking__payments__status='completed'
            ).select_related('booking', 'airline')
            
            outstanding_items = []
            total_outstanding = Decimal('0.00')
            
            for ticket in unpaid_tickets:
                # Calculate days outstanding
                days_outstanding = (timezone.now().date() - ticket.issued_at.date()).days
                
                # Determine aging category
                if days_outstanding <= 7:
                    aging = '0-7 days'
                elif days_outstanding <= 30:
                    aging = '8-30 days'
                elif days_outstanding <= 60:
                    aging = '31-60 days'
                elif days_outstanding <= 90:
                    aging = '61-90 days'
                else:
                    aging = '90+ days (Overdue)'
                
                item = {
                    'ticket_number': ticket.ticket_number,
                    'booking_reference': ticket.booking.booking_reference,
                    'passenger_name': ticket.passenger_name,
                    'airline': ticket.airline.name if ticket.airline else '',
                    'route': f"{ticket.origin} - {ticket.destination}",
                    'issue_date': ticket.issued_at.strftime('%Y-%m-%d'),
                    'amount': ticket.total_amount,
                    'currency': ticket.currency,
                    'days_outstanding': days_outstanding,
                    'aging_category': aging,
                    'status': ticket.status
                }
                
                outstanding_items.append(item)
                total_outstanding += ticket.total_amount
            
            # Group by aging
            aging_summary = {
                '0-7 days': Decimal('0.00'),
                '8-30 days': Decimal('0.00'),
                '31-60 days': Decimal('0.00'),
                '61-90 days': Decimal('0.00'),
                '90+ days (Overdue)': Decimal('0.00')
            }
            
            for item in outstanding_items:
                aging_summary[item['aging_category']] += item['amount']
            
            return {
                'success': True,
                'agent_name': agent.get_full_name(),
                'total_outstanding': total_outstanding,
                'outstanding_count': len(outstanding_items),
                'outstanding_items': outstanding_items,
                'aging_summary': aging_summary,
                'generated_at': timezone.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting outstanding details: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def get_payment_history(self, agent, days=30):
        """
        Get payment history for an agent
        """
        try:
            from accounts.models.transaction_tracking import TransactionLog
            from datetime import timedelta
            
            start_date = timezone.now() - timedelta(days=days)
            
            payments = TransactionLog.objects.filter(
                agent=agent,
                transaction_type='payment_received',
                status='completed',
                transaction_date__gte=start_date
            ).order_by('-transaction_date')
            
            payment_list = []
            total_paid = Decimal('0.00')
            
            for payment in payments:
                payment_list.append({
                    'transaction_number': payment.transaction_number,
                    'date': payment.transaction_date.strftime('%Y-%m-%d %H:%M'),
                    'amount': payment.total_amount,
                    'currency': payment.currency,
                    'description': payment.description,
                    'reference': payment.journal_entry_reference,
                    'booking_reference': payment.booking.booking_reference if payment.booking else ''
                })
                total_paid += payment.total_amount
            
            return {
                'success': True,
                'agent_name': agent.get_full_name(),
                'period_days': days,
                'total_payments': len(payment_list),
                'total_amount_paid': total_paid,
                'payments': payment_list,
                'generated_at': timezone.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting payment history: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def check_credit_limit(self, agent, requested_amount):
        """
        Check if agent has sufficient credit for a transaction
        """
        try:
            balance_info = self.get_agent_balance(agent)
            
            if not balance_info['success']:
                return {'allowed': False, 'reason': 'Unable to check balance'}
            
            available_credit = balance_info['available_credit']
            
            if requested_amount <= available_credit:
                return {
                    'allowed': True,
                    'available_credit': available_credit,
                    'requested_amount': requested_amount,
                    'remaining_credit': available_credit - requested_amount
                }
            else:
                return {
                    'allowed': False,
                    'reason': 'Insufficient credit',
                    'available_credit': available_credit,
                    'requested_amount': requested_amount,
                    'shortfall': requested_amount - available_credit
                }
                
        except Exception as e:
            logger.error(f"Error checking credit limit: {str(e)}", exc_info=True)
            return {'allowed': False, 'reason': str(e)}
    
    def get_all_agents_balances(self):
        """
        Get balance summary for all agents (for staff/admin)
        """
        try:
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            
            agents = User.objects.filter(
                user_type__in=['agent', 'super_agent'],
                is_active=True
            )
            
            summary = []
            total_outstanding = Decimal('0.00')
            total_credit_limit = Decimal('0.00')
            
            for agent in agents:
                balance_info = self.get_agent_balance(agent)
                
                if balance_info['success']:
                    agent_summary = {
                        'agent_id': str(agent.id),
                        'agent_name': agent.get_full_name(),
                        'agent_code': agent.agent_code if hasattr(agent, 'agent_code') else '',
                        'email': agent.email,
                        'phone': agent.phone_number,
                        'current_balance': balance_info['current_balance'],
                        'outstanding_amount': balance_info['outstanding_amount'],
                        'credit_limit': balance_info['credit_limit'],
                        'available_credit': balance_info['available_credit'],
                        'credit_utilization': (
                            (balance_info['outstanding_amount'] / balance_info['credit_limit'] * 100)
                            if balance_info['credit_limit'] > 0 else 0
                        ),
                        'last_transaction': balance_info['last_transaction_date']
                    }
                    
                    summary.append(agent_summary)
                    total_outstanding += balance_info['outstanding_amount']
                    total_credit_limit += balance_info['credit_limit']
            
            return {
                'success': True,
                'total_agents': len(summary),
                'total_outstanding': total_outstanding,
                'total_credit_limit': total_credit_limit,
                'total_available_credit': total_credit_limit - total_outstanding,
                'agents': summary,
                'generated_at': timezone.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting all agents balances: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def record_payment(self, agent, amount, payment_method, reference, notes=''):
        """
        Record a payment from agent (updates balance automatically via signals)
        """
        try:
            with transaction.atomic():
                from accounts.models.transaction_tracking import TransactionLog
                
                # Create payment transaction
                payment_trans = TransactionLog.objects.create(
                    transaction_type='payment_received',
                    status='completed',
                    agent=agent,
                    base_amount=amount,
                    total_amount=amount,
                    currency='SAR',
                    description=f"Payment received via {payment_method}",
                    notes=notes,
                    transaction_date=timezone.now(),
                    metadata={
                        'payment_method': payment_method,
                        'reference': reference
                    }
                )
                
                # Signal will automatically:
                # 1. Update agent ledger
                # 2. Post to accounting
                # 3. Update daily summary
                
                logger.info(f"Payment recorded for {agent.get_full_name()}: {amount}")
                
                return {
                    'success': True,
                    'transaction_number': payment_trans.transaction_number,
                    'amount': amount,
                    'message': 'Payment recorded successfully'
                }
                
        except Exception as e:
            logger.error(f"Error recording payment: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def get_credit_utilization_report(self):
        """
        Get credit utilization report for all agents
        """
        try:
            all_balances = self.get_all_agents_balances()
            
            if not all_balances['success']:
                return all_balances
            
            # Categorize agents by credit utilization
            categories = {
                'healthy': [],      # 0-50%
                'moderate': [],     # 51-75%
                'high': [],         # 76-90%
                'critical': []      # 91-100%
            }
            
            for agent in all_balances['agents']:
                utilization = agent['credit_utilization']
                
                if utilization <= 50:
                    categories['healthy'].append(agent)
                elif utilization <= 75:
                    categories['moderate'].append(agent)
                elif utilization <= 90:
                    categories['high'].append(agent)
                else:
                    categories['critical'].append(agent)
            
            return {
                'success': True,
                'summary': {
                    'healthy_count': len(categories['healthy']),
                    'moderate_count': len(categories['moderate']),
                    'high_count': len(categories['high']),
                    'critical_count': len(categories['critical'])
                },
                'categories': categories,
                'generated_at': timezone.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting credit utilization report: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
