# accounts/urls/accounting_urls.py
"""
URL patterns for accounting module
"""

from django.urls import path
from accounts.views import (
    accounting_dashboard, account_list, journal_entries, trial_balance,
    create_account, accounting_rules, financial_reports,
    toggle_account_status, account_detail
)

app_name = 'accounting'

urlpatterns = [
    # Dashboard
    path('', accounting_dashboard, name='dashboard'),

    # Accounts
    path('accounts/', account_list, name='account_list'),
    path('accounts/create/', create_account, name='create_account'),
    path('accounts/<uuid:account_id>/', account_detail, name='account_detail'),
    path('accounts/<uuid:account_id>/toggle/', toggle_account_status, name='toggle_account_status'),

    # Journal Entries
    path('journal/', journal_entries, name='journal_entries'),

    # Reports
    path('reports/trial-balance/', trial_balance, name='trial_balance'),
    path('reports/', financial_reports, name='reports'),

    # Rules
    path('rules/', accounting_rules, name='rules'),
]