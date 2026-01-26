# accounts/views/accounting_views.py
"""
Accounting views for B2B platform
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from decimal import Decimal

from accounts.models import (
    Account, JournalEntry, AccountingPeriod, AccountingRule, FinancialReport
)
from accounts.services import AccountingService
from accounts.decorators import require_business_unit, require_permission


@login_required
@require_business_unit
@require_permission('view_accounting')
def accounting_dashboard(request):
    """Main accounting dashboard"""
    context = {
        'title': 'Accounting Dashboard',
        'total_accounts': Account.objects.filter(is_active=True).count(),
        'total_entries': JournalEntry.objects.count(),
        'recent_entries': JournalEntry.objects.select_related(
            'account', 'user', 'booking'
        ).order_by('-created_at')[:10],
    }

    # Calculate current period totals
    current_date = timezone.now().date()
    context['trial_balance'] = AccountingService.get_trial_balance(current_date)

    return render(request, 'accounts/accounting/dashboard.html', context)


@login_required
@require_business_unit
@require_permission('view_accounts')
def account_list(request):
    """List all accounts"""
    accounts = Account.objects.filter(is_active=True).order_by('code')

    # Calculate balances
    for account in accounts:
        account.current_balance = account.get_balance()

    context = {
        'title': 'Chart of Accounts',
        'accounts': accounts,
    }

    return render(request, 'accounts/accounting/account_list.html', context)


@login_required
@require_business_unit
@require_permission('view_journal_entries')
def journal_entries(request):
    """List journal entries with filtering"""
    entries = JournalEntry.objects.select_related(
        'account', 'user', 'booking', 'ticket', 'payment'
    ).order_by('-date', '-created_at')

    # Apply filters
    transaction_type = request.GET.get('transaction_type')
    account_code = request.GET.get('account')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if transaction_type:
        entries = entries.filter(transaction_type=transaction_type)

    if account_code:
        entries = entries.filter(account__code=account_code)

    if date_from:
        entries = entries.filter(date__gte=date_from)

    if date_to:
        entries = entries.filter(date__lte=date_to)

    # Pagination
    paginator = Paginator(entries, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': 'Journal Entries',
        'page_obj': page_obj,
        'transaction_types': JournalEntry.TransactionType.choices,
        'accounts': Account.objects.filter(is_active=True).order_by('code'),
        'filters': {
            'transaction_type': transaction_type,
            'account': account_code,
            'date_from': date_from,
            'date_to': date_to,
        }
    }

    return render(request, 'accounts/accounting/journal_entries.html', context)


@login_required
@require_business_unit
@require_permission('view_reports')
def trial_balance(request):
    """Generate trial balance report"""
    as_of_date = request.GET.get('date')
    if not as_of_date:
        as_of_date = timezone.now().date()

    trial_balance = AccountingService.get_trial_balance(as_of_date)

    context = {
        'title': 'Trial Balance',
        'trial_balance': trial_balance,
        'as_of_date': as_of_date,
    }

    return render(request, 'accounts/accounting/trial_balance.html', context)


@login_required
@require_business_unit
@require_permission('manage_accounts')
def create_account(request):
    """Create new account"""
    if request.method == 'POST':
        code = request.POST.get('code')
        name = request.POST.get('name')
        account_type = request.POST.get('account_type')
        category = request.POST.get('category')
        normal_balance = request.POST.get('normal_balance')
        description = request.POST.get('description', '')

        try:
            account = Account.objects.create(
                code=code,
                name=name,
                account_type=account_type,
                category=category,
                normal_balance=normal_balance,
                description=description
            )
            messages.success(request, f'Account {account} created successfully')
            return redirect('accounting:account_list')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')

    context = {
        'title': 'Create Account',
        'account_types': Account.AccountType.choices,
        'categories': Account.AccountCategory.choices,
        'normal_balances': [('debit', 'Debit'), ('credit', 'Credit')],
    }

    return render(request, 'accounts/accounting/create_account.html', context)


@login_required
@require_business_unit
@require_permission('manage_accounting_rules')
def accounting_rules(request):
    """Manage accounting rules"""
    rules = AccountingRule.objects.all().order_by('rule_type')

    context = {
        'title': 'Accounting Rules',
        'rules': rules,
    }

    return render(request, 'accounts/accounting/rules.html', context)


@login_required
@require_business_unit
@require_permission('view_reports')
def financial_reports(request):
    """List financial reports"""
    reports = FinancialReport.objects.select_related(
        'generated_by', 'period'
    ).order_by('-generated_at')

    context = {
        'title': 'Financial Reports',
        'reports': reports,
    }

    return render(request, 'accounts/accounting/reports.html', context)


@require_POST
@login_required
@require_business_unit
@require_permission('manage_accounts')
def toggle_account_status(request, account_id):
    """Toggle account active status"""
    account = get_object_or_404(Account, id=account_id)

    account.is_active = not account.is_active
    account.save()

    status = 'activated' if account.is_active else 'deactivated'
    messages.success(request, f'Account {account} {status}')

    return JsonResponse({'success': True, 'is_active': account.is_active})


@login_required
@require_business_unit
@require_permission('view_accounting')
def account_detail(request, account_id):
    """Account detail with transaction history"""
    account = get_object_or_404(Account, id=account_id)

    # Get entries for this account
    entries = JournalEntry.objects.filter(
        account=account
    ).select_related('user', 'booking').order_by('-date', '-created_at')

    # Calculate running balance
    running_balance = Decimal('0.00')
    for entry in entries:
        if account.normal_balance == 'debit':
            if entry.entry_type == 'debit':
                running_balance += entry.amount
            else:
                running_balance -= entry.amount
        else:
            if entry.entry_type == 'credit':
                running_balance += entry.amount
            else:
                running_balance -= entry.amount
        entry.running_balance = running_balance

    # Current balance
    current_balance = account.get_balance()

    context = {
        'title': f'Account Detail: {account}',
        'account': account,
        'entries': entries[:100],  # Limit to last 100 entries
        'current_balance': current_balance,
    }

    return render(request, 'accounts/accounting/account_detail.html', context)