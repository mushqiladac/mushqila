"""
Finance App Web Views for PC Interface
Flutter mobile app এর পাশাপাশি PC web interface জন্য
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Sum, Count, Q
from rest_framework import status
from ..models.user import FinanceUser
from ..models import FinanceTransaction, TicketSale, SalesSubmission
from ..serializers import (
    FinanceTransactionSerializer, 
    TicketSaleSerializer,
    SalesSubmissionSerializer
)


def finance_login(request):
    """Finance App Login Page for PC Users"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        if user is not None and hasattr(user, 'financeuser'):
            login(request, user)
            messages.success(request, 'সফলভাবে লগইন হয়েছে!')
            return redirect('finance:dashboard')
        else:
            messages.error(request, 'ভুল ইমেল বা পাসওয়ার্ড')
    
    return render(request, 'finance/login.html')


@login_required
def finance_logout(request):
    """Finance App Logout"""
    logout(request)
    messages.success(request, 'সফলভাবে লগআউট হয়েছে!')
    return redirect('finance:login')


@login_required
def finance_dashboard(request):
    """Finance App Dashboard for PC Users"""
    user = request.user.financeuser
    
    # Dashboard data
    today = timezone.now().date()
    
    # Today's sales
    today_sales = FinanceTransaction.objects.filter(
        user=user,
        transaction_type='sale',
        created_at__date=today
    ).aggregate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    # This month's sales
    this_month_sales = FinanceTransaction.objects.filter(
        user=user,
        transaction_type='sale',
        created_at__month=today.month,
        created_at__year=today.year
    ).aggregate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    # Recent transactions
    recent_transactions = FinanceTransaction.objects.filter(
        user=user
    ).order_by('-created_at')[:10]
    
    # Pending submissions (if user is manager)
    pending_submissions = []
    if user.user_type in ['admin', 'manager']:
        pending_submissions = SalesSubmission.objects.filter(
            status='pending'
        ).order_by('-submitted_at')[:10]
    
    context = {
        'user': user,
        'today_sales': today_sales,
        'this_month_sales': this_month_sales,
        'recent_transactions': recent_transactions,
        'pending_submissions': pending_submissions,
    }
    
    return render(request, 'finance/dashboard.html', context)


@login_required
def ticket_list(request):
    """Ticket List for PC Users"""
    user = request.user.financeuser
    tickets = TicketSale.objects.filter(user=user).order_by('-created_at')
    
    context = {
        'tickets': tickets,
        'user': user,
    }
    
    return render(request, 'finance/tickets/list.html', context)


@login_required
def ticket_create(request):
    """Create New Ticket for PC Users"""
    user = request.user.financeuser
    
    if request.method == 'POST':
        # Get form data
        pnr = request.POST.get('pnr')
        ticket_number = request.POST.get('ticket_number')
        airline_id = request.POST.get('airline')
        passenger_name = request.POST.get('passenger_name')
        customer_price = request.POST.get('customer_price')
        airline_cost = request.POST.get('airline_cost')
        payment_method = request.POST.get('payment_method')
        
        # Create ticket
        try:
            ticket = TicketSale.objects.create(
                user=user,
                pnr=pnr,
                ticket_number=ticket_number,
                airline_id=airline_id,
                passenger_name=passenger_name,
                customer_price=customer_price,
                airline_cost=airline_cost,
                payment_method=payment_method,
                status='active'
            )
            
            messages.success(request, 'টিকেট সফলভাবে তৈরি হয়েছে!')
            return redirect('finance:ticket_list')
            
        except Exception as e:
            messages.error(request, f'টিকেট তৈরিতে সমস্যা: {str(e)}')
    
    # Get airlines and payment methods for dropdown
    from ..models import Airline, PaymentMethod
    airlines = Airline.objects.filter(is_active=True)
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    
    context = {
        'airlines': airlines,
        'payment_methods': payment_methods,
        'user': user,
    }
    
    return render(request, 'finance/tickets/create.html', context)


@login_required
def submission_list(request):
    """Submissions List for PC Users"""
    user = request.user.financeuser
    
    if user.user_type in ['admin', 'manager']:
        submissions = SalesSubmission.objects.all().order_by('-submitted_at')
    else:
        submissions = SalesSubmission.objects.filter(user=user).order_by('-submitted_at')
    
    context = {
        'submissions': submissions,
        'user': user,
        'is_manager': user.user_type in ['admin', 'manager'],
    }
    
    return render(request, 'finance/submissions/list.html', context)


@login_required
def submission_detail(request, submission_id):
    """Submission Detail and Approval for PC Users"""
    user = request.user.financeuser
    
    try:
        submission = SalesSubmission.objects.get(id=submission_id)
        
        # Check permissions
        if user.user_type not in ['admin', 'manager'] and submission.user != user:
            messages.error(request, 'আপনার এই submission দেখার অনুমতি নেই')
            return redirect('finance:submission_list')
        
        if request.method == 'POST' and user.user_type in ['admin', 'manager']:
            action = request.POST.get('action')
            
            if action == 'approve':
                submission.status = 'approved'
                submission.reviewed_by = user
                submission.reviewed_at = timezone.now()
                submission.save()
                messages.success(request, 'Submission অনুমোদন করা হয়েছে!')
                
            elif action == 'reject':
                submission.status = 'rejected'
                submission.reviewed_by = user
                submission.reviewed_at = timezone.now()
                submission.save()
                messages.success(request, 'Submission বাতিল করা হয়েছে!')
        
        context = {
            'submission': submission,
            'user': user,
            'can_approve': user.user_type in ['admin', 'manager'],
        }
        
        return render(request, 'finance/submissions/detail.html', context)
        
    except SalesSubmission.DoesNotExist:
        messages.error(request, 'Submission পাওয়া যায়নি')
        return redirect('finance:submission_list')


@login_required
def profile_view(request):
    """User Profile for PC Users"""
    user = request.user.financeuser
    
    context = {
        'user': user,
    }
    
    return render(request, 'finance/profile.html', context)


@require_POST
@login_required
def update_profile(request):
    """Update User Profile"""
    user = request.user.financeuser
    
    try:
        # Update user fields
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        user.alternative_email = request.POST.get('alternative_email', user.alternative_email)
        
        user.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'প্রোফাইল সফলভাবে আপডেট হয়েছে!'})
        
        messages.success(request, 'প্রোফাইল সফলভাবে আপডেট হয়েছে!')
        return redirect('finance:profile')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': str(e)})
        
        messages.error(request, f'প্রোফাইল আপডেটে সমস্যা: {str(e)}')
        return redirect('finance:profile')
