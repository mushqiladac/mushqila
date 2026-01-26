# accounts/services/accounting_service.py
"""
Automatic Accounting Service for B2B Travel Platform
Handles all financial accounting operations automatically
"""

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from typing import Dict, List, Optional, Any
import logging

from accounts.models import (
    Account, JournalEntry, AccountingRule, AccountingPeriod,
    BusinessUnit, User, AuditLog
)
from flights.models import Booking, Ticket, Payment, Refund

logger = logging.getLogger(__name__)


class AccountingService:
    """Service for automatic accounting entries"""

    @staticmethod
    def get_or_create_reference_number(transaction_type: str, entity_id: str) -> str:
        """Generate unique reference number for journal entries"""
        date_str = timezone.now().strftime('%Y%m%d')
        return f"{transaction_type.upper()}-{date_str}-{entity_id[:8]}"

    @staticmethod
    def get_account_by_code(code: str) -> Optional[Account]:
        """Get account by code"""
        try:
            return Account.objects.get(code=code, is_active=True)
        except Account.DoesNotExist:
            logger.error(f"Account with code {code} not found")
            return None

    @staticmethod
    def create_journal_entries(
        transaction_type: str,
        description: str,
        user: User,
        debit_entries: List[Dict[str, Any]],
        credit_entries: List[Dict[str, Any]],
        booking: Optional[Booking] = None,
        ticket: Optional[Ticket] = None,
        payment: Optional[Payment] = None
    ) -> List[JournalEntry]:
        """
        Create balanced journal entries (debits = credits)
        """
        entries = []
        total_debit = Decimal('0.00')
        total_credit = Decimal('0.00')

        # Create debit entries
        for debit in debit_entries:
            account = AccountingService.get_account_by_code(debit['account_code'])
            if not account:
                raise ValidationError(f"Invalid debit account code: {debit['account_code']}")

            amount = Decimal(str(debit['amount']))
            total_debit += amount

            entry = JournalEntry.objects.create(
                reference_number=AccountingService.get_or_create_reference_number(
                    transaction_type, str(uuid.uuid4())
                ),
                transaction_type=transaction_type,
                description=description,
                user=user,
                booking=booking,
                ticket=ticket,
                payment=payment,
                account=account,
                entry_type='debit',
                amount=amount,
                created_by=user
            )
            entries.append(entry)

        # Create credit entries
        for credit in credit_entries:
            account = AccountingService.get_account_by_code(credit['account_code'])
            if not account:
                raise ValidationError(f"Invalid credit account code: {credit['account_code']}")

            amount = Decimal(str(credit['amount']))
            total_credit += amount

            entry = JournalEntry.objects.create(
                reference_number=AccountingService.get_or_create_reference_number(
                    transaction_type, str(uuid.uuid4())
                ),
                transaction_type=transaction_type,
                description=description,
                user=user,
                booking=booking,
                ticket=ticket,
                payment=payment,
                account=account,
                entry_type='credit',
                amount=amount,
                created_by=user
            )
            entries.append(entry)

        # Validate double-entry balance
        if total_debit != total_credit:
            # Rollback entries if unbalanced
            for entry in entries:
                entry.delete()
            raise ValidationError(
                f"Unbalanced journal entries: Debits {total_debit} != Credits {total_credit}"
            )

        return entries

    @staticmethod
    def record_ticket_issue(ticket: Ticket, user: User) -> List[JournalEntry]:
        """Record accounting entries for ticket issuance"""
        try:
            with transaction.atomic():
                # Get accounting rule
                rule = AccountingRule.objects.get(
                    rule_type='ticket_issue',
                    is_active=True
                )

                # Calculate amounts
                ticket_amount = ticket.total_amount
                commission_amount = ticket.commission_amount or Decimal('0.00')

                # Prepare debit entries
                debit_entries = []
                for debit in rule.debit_entries:
                    if debit['amount_field'] == 'ticket_amount':
                        amount = ticket_amount
                    elif debit['amount_field'] == 'commission_amount':
                        amount = commission_amount
                    else:
                        amount = Decimal('0.00')

                    debit_entries.append({
                        'account_code': debit['account_code'],
                        'amount': amount
                    })

                # Prepare credit entries
                credit_entries = []
                for credit in rule.credit_entries:
                    if credit['amount_field'] == 'ticket_amount':
                        amount = ticket_amount
                    elif credit['amount_field'] == 'commission_amount':
                        amount = commission_amount
                    else:
                        amount = Decimal('0.00')

                    credit_entries.append({
                        'account_code': credit['account_code'],
                        'amount': amount
                    })

                description = f"Ticket issued: {ticket.pnr} - {ticket.passenger_name}"

                entries = AccountingService.create_journal_entries(
                    'ticket_issue',
                    description,
                    user,
                    debit_entries,
                    credit_entries,
                    booking=ticket.booking,
                    ticket=ticket
                )

                # Log audit
                AuditLog.objects.create(
                    user=user,
                    action='ticket_issue_accounting',
                    resource_type='ticket',
                    resource_id=str(ticket.id),
                    details={'entries_count': len(entries), 'total_amount': str(ticket_amount)}
                )

                logger.info(f"Recorded accounting for ticket issue: {ticket.pnr}")
                return entries

        except AccountingRule.DoesNotExist:
            logger.warning(f"No accounting rule found for ticket issue")
            return []
        except Exception as e:
            logger.error(f"Error recording ticket issue accounting: {str(e)}")
            raise

    @staticmethod
    def record_ticket_void(ticket: Ticket, user: User) -> List[JournalEntry]:
        """Record accounting entries for ticket voiding"""
        try:
            with transaction.atomic():
                # Get accounting rule
                rule = AccountingRule.objects.get(
                    rule_type='ticket_void',
                    is_active=True
                )

                ticket_amount = ticket.total_amount
                commission_amount = ticket.commission_amount or Decimal('0.00')

                # Reverse the original entries (credit what was debited, debit what was credited)
                debit_entries = []
                for credit in rule.debit_entries:  # Original debits become credits
                    if credit['amount_field'] == 'ticket_amount':
                        amount = ticket_amount
                    elif credit['amount_field'] == 'commission_amount':
                        amount = commission_amount
                    else:
                        amount = Decimal('0.00')

                    debit_entries.append({
                        'account_code': credit['account_code'],
                        'amount': amount
                    })

                credit_entries = []
                for debit in rule.credit_entries:  # Original credits become debits
                    if debit['amount_field'] == 'ticket_amount':
                        amount = ticket_amount
                    elif debit['amount_field'] == 'commission_amount':
                        amount = commission_amount
                    else:
                        amount = Decimal('0.00')

                    credit_entries.append({
                        'account_code': debit['account_code'],
                        'amount': amount
                    })

                description = f"Ticket voided: {ticket.pnr} - {ticket.passenger_name}"

                entries = AccountingService.create_journal_entries(
                    'ticket_void',
                    description,
                    user,
                    debit_entries,
                    credit_entries,
                    booking=ticket.booking,
                    ticket=ticket
                )

                # Log audit
                AuditLog.objects.create(
                    user=user,
                    action='ticket_void_accounting',
                    resource_type='ticket',
                    resource_id=str(ticket.id),
                    details={'entries_count': len(entries), 'total_amount': str(ticket_amount)}
                )

                logger.info(f"Recorded accounting for ticket void: {ticket.pnr}")
                return entries

        except AccountingRule.DoesNotExist:
            logger.warning(f"No accounting rule found for ticket void")
            return []
        except Exception as e:
            logger.error(f"Error recording ticket void accounting: {str(e)}")
            raise

    @staticmethod
    def record_ticket_cancel(ticket: Ticket, user: User) -> List[JournalEntry]:
        """Record accounting entries for ticket cancellation"""
        try:
            with transaction.atomic():
                # Get accounting rule
                rule = AccountingRule.objects.get(
                    rule_type='ticket_cancel',
                    is_active=True
                )

                ticket_amount = ticket.total_amount
                commission_amount = ticket.commission_amount or Decimal('0.00')

                # Similar to void but may have different accounts
                debit_entries = []
                for debit in rule.debit_entries:
                    if debit['amount_field'] == 'ticket_amount':
                        amount = ticket_amount
                    elif debit['amount_field'] == 'commission_amount':
                        amount = commission_amount
                    else:
                        amount = Decimal('0.00')

                    debit_entries.append({
                        'account_code': debit['account_code'],
                        'amount': amount
                    })

                credit_entries = []
                for credit in rule.credit_entries:
                    if credit['amount_field'] == 'ticket_amount':
                        amount = ticket_amount
                    elif credit['amount_field'] == 'commission_amount':
                        amount = commission_amount
                    else:
                        amount = Decimal('0.00')

                    credit_entries.append({
                        'account_code': credit['account_code'],
                        'amount': amount
                    })

                description = f"Ticket cancelled: {ticket.pnr} - {ticket.passenger_name}"

                entries = AccountingService.create_journal_entries(
                    'ticket_cancel',
                    description,
                    user,
                    debit_entries,
                    credit_entries,
                    booking=ticket.booking,
                    ticket=ticket
                )

                # Log audit
                AuditLog.objects.create(
                    user=user,
                    action='ticket_cancel_accounting',
                    resource_type='ticket',
                    resource_id=str(ticket.id),
                    details={'entries_count': len(entries), 'total_amount': str(ticket_amount)}
                )

                logger.info(f"Recorded accounting for ticket cancel: {ticket.pnr}")
                return entries

        except AccountingRule.DoesNotExist:
            logger.warning(f"No accounting rule found for ticket cancel")
            return []
        except Exception as e:
            logger.error(f"Error recording ticket cancel accounting: {str(e)}")
            raise

    @staticmethod
    def record_ticket_refund(refund: Refund, user: User) -> List[JournalEntry]:
        """Record accounting entries for ticket refund"""
        try:
            with transaction.atomic():
                # Get accounting rule
                rule = AccountingRule.objects.get(
                    rule_type='ticket_refund',
                    is_active=True
                )

                refund_amount = refund.refund_amount
                fee_amount = refund.processing_fee or Decimal('0.00')

                # Prepare debit entries
                debit_entries = []
                for debit in rule.debit_entries:
                    if debit['amount_field'] == 'refund_amount':
                        amount = refund_amount
                    elif debit['amount_field'] == 'fee_amount':
                        amount = fee_amount
                    else:
                        amount = Decimal('0.00')

                    debit_entries.append({
                        'account_code': debit['account_code'],
                        'amount': amount
                    })

                # Prepare credit entries
                credit_entries = []
                for credit in rule.credit_entries:
                    if credit['amount_field'] == 'refund_amount':
                        amount = refund_amount
                    elif credit['amount_field'] == 'fee_amount':
                        amount = fee_amount
                    else:
                        amount = Decimal('0.00')

                    credit_entries.append({
                        'account_code': credit['account_code'],
                        'amount': amount
                    })

                description = f"Ticket refund: {refund.ticket.pnr} - {refund.ticket.passenger_name}"

                entries = AccountingService.create_journal_entries(
                    'ticket_refund',
                    description,
                    user,
                    debit_entries,
                    credit_entries,
                    booking=refund.ticket.booking,
                    ticket=refund.ticket,
                    payment=refund.payment
                )

                # Log audit
                AuditLog.objects.create(
                    user=user,
                    action='ticket_refund_accounting',
                    resource_type='refund',
                    resource_id=str(refund.id),
                    details={'entries_count': len(entries), 'refund_amount': str(refund_amount)}
                )

                logger.info(f"Recorded accounting for ticket refund: {refund.ticket.pnr}")
                return entries

        except AccountingRule.DoesNotExist:
            logger.warning(f"No accounting rule found for ticket refund")
            return []
        except Exception as e:
            logger.error(f"Error recording ticket refund accounting: {str(e)}")
            raise

    @staticmethod
    def record_payment_received(payment: Payment, user: User) -> List[JournalEntry]:
        """Record accounting entries for payment received"""
        try:
            with transaction.atomic():
                # Get accounting rule
                rule = AccountingRule.objects.get(
                    rule_type='payment_received',
                    is_active=True
                )

                payment_amount = payment.amount

                # Debit cash/receivable, credit revenue
                debit_entries = [{
                    'account_code': '1001',  # Cash account
                    'amount': payment_amount
                }]

                credit_entries = [{
                    'account_code': '4001',  # Accounts receivable or revenue
                    'amount': payment_amount
                }]

                description = f"Payment received: {payment.reference_number}"

                entries = AccountingService.create_journal_entries(
                    'payment_received',
                    description,
                    user,
                    debit_entries,
                    credit_entries,
                    booking=payment.booking,
                    payment=payment
                )

                # Log audit
                AuditLog.objects.create(
                    user=user,
                    action='payment_received_accounting',
                    resource_type='payment',
                    resource_id=str(payment.id),
                    details={'entries_count': len(entries), 'amount': str(payment_amount)}
                )

                logger.info(f"Recorded accounting for payment received: {payment.reference_number}")
                return entries

        except AccountingRule.DoesNotExist:
            logger.warning(f"No accounting rule found for payment received")
            return []
        except Exception as e:
            logger.error(f"Error recording payment accounting: {str(e)}")
            raise

    @staticmethod
    def get_account_balance(account_code: str, as_of_date=None) -> Decimal:
        """Get account balance as of given date"""
        account = AccountingService.get_account_by_code(account_code)
        if not account:
            return Decimal('0.00')
        return account.get_balance(as_of_date)

    @staticmethod
    def get_trial_balance(as_of_date=None) -> Dict[str, Any]:
        """Generate trial balance report"""
        if as_of_date is None:
            as_of_date = timezone.now().date()

        accounts = Account.objects.filter(is_active=True)
        trial_balance = {
            'date': as_of_date,
            'accounts': [],
            'totals': {
                'debit': Decimal('0.00'),
                'credit': Decimal('0.00')
            }
        }

        for account in accounts:
            balance = account.get_balance(as_of_date)
            if balance != 0:
                account_data = {
                    'code': account.code,
                    'name': account.name,
                    'type': account.account_type,
                    'balance': balance,
                    'balance_type': 'debit' if balance > 0 else 'credit'
                }
                trial_balance['accounts'].append(account_data)

                if balance > 0:
                    trial_balance['totals']['debit'] += balance
                else:
                    trial_balance['totals']['credit'] += abs(balance)

        return trial_balance