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
        selected_user_type = request.POST.get('user_type')
        
        # Try to authenticate with FinanceUser first
        try:
            from finance.models.user import FinanceUser
            finance_user = FinanceUser.objects.get(email=email)
            
            if finance_user.check_password(password) and finance_user.is_active:
                # Check if the selected user type matches
                if finance_user.user_type == selected_user_type:
                    # Create or get corresponding accounts.User for session authentication
                    from accounts.models import User
                    try:
                        # Try to get existing User
                        user = User.objects.get(email=email)
                    except User.DoesNotExist:
                        # Create a linked User account for session authentication
                        user = User.objects.create(
                            email=email,
                            username=email,
                            first_name=finance_user.first_name,
                            last_name=finance_user.last_name,
                            phone=finance_user.phone if finance_user.phone else '+966500000000',
                            user_type='admin',  # Finance users are admins
                            is_staff=True,
                            is_active=True
                        )
                        user.set_password(password)
                        user.save()
                    
                    # Now login with the accounts.User
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    
                    # Store finance user info in session
                    request.session['finance_user_id'] = finance_user.id
                    request.session['finance_user_type'] = finance_user.user_type
                    
                    messages.success(request, 'সফলভাবে লগইন হয়েছে!')
                    return redirect('finance:dashboard')
                else:
                    messages.error(request, f'নির্বাচিত ইউজার টাইপ মেলেনি। আপনি {selected_user_type} নির্বাচন করেছেন কিন্তু এই ইউজার {finance_user.get_user_type_display()}।')
            else:
                messages.error(request, 'ভুল ইমেল বা পাসওয়ার্ড')
        except FinanceUser.DoesNotExist:
            messages.error(request, 'ভুল ইমেল বা পাসওয়ার্ড')
        except Exception as e:
            messages.error(request, f'লগইন সমস্যা: {str(e)}')
    
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
    user = request.user
    
    # Get finance user from session
    finance_user_id = request.session.get('finance_user_id')
    finance_user_type = request.session.get('finance_user_type', 'user')
    
    # Get FinanceUser if exists
    finance_user = None
    if finance_user_id:
        try:
            from finance.models.user import FinanceUser
            finance_user = FinanceUser.objects.get(id=finance_user_id)
        except:
            pass
    
    # Dashboard data
    today = timezone.now().date()
    
    # Today's sales
    today_sales = {'total': 0, 'count': 0}
    this_month_sales = {'total': 0, 'count': 0}
    recent_transactions = []
    pending_submissions = []
    
    # Try to get finance transactions if FinanceUser exists
    if finance_user:
        try:
            today_sales = FinanceTransaction.objects.filter(
                user=finance_user,
                transaction_type='sale',
                created_at__date=today
            ).aggregate(
                total=Sum('amount'),
                count=Count('id')
            )
            
            this_month_sales = FinanceTransaction.objects.filter(
                user=finance_user,
                transaction_type='sale',
                created_at__month=today.month,
                created_at__year=today.year
            ).aggregate(
                total=Sum('amount'),
                count=Count('id')
            )
            
            recent_transactions = FinanceTransaction.objects.filter(
                user=finance_user
            ).order_by('-created_at')[:10]
            
            # Pending submissions (if user is manager)
            if finance_user_type in ['admin', 'manager']:
                pending_submissions = SalesSubmission.objects.filter(
                    status='pending'
                ).order_by('-submitted_at')[:10]
        except:
            pass
    
    context = {
        'user': user,
        'finance_user': finance_user,
        'finance_user_type': finance_user_type,
        'today_sales': today_sales,
        'this_month_sales': this_month_sales,
        'recent_transactions': recent_transactions,
        'pending_submissions': pending_submissions,
    }
    
    return render(request, 'finance/dashboard.html', context)


@login_required
def ticket_list(request):
    """Ticket List for PC Users"""
    user = request.user
    tickets = TicketSale.objects.filter(user=user).order_by('-created_at')
    
    context = {
        'tickets': tickets,
        'user': user,
    }
    
    return render(request, 'finance/tickets/list.html', context)


@login_required
def ticket_create(request):
    """Create New Ticket for PC Users"""
    user = request.user
    
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
    user = request.user
    
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
    user = request.user
    
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
    user = request.user
    
    context = {
        'user': user,
    }
    
    return render(request, 'finance/profile.html', context)


@login_required
def create_user(request):
    """Create new user (Admin/Manager only)"""
    user = request.user
    
    # Check if user has permission to create users
    if user.user_type not in ['admin', 'manager']:
        messages.error(request, 'আপনার ইউজার তৈরির অনুমতি নেই। শুধুমাত্র Admin বা Manager ইউজার তৈরি করতে পারে।')
        return redirect('finance:dashboard')
    
    if request.method == 'POST':
        from ..models.user import FinanceUser
        from ..serializers.user import RegisterSerializer
        
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            new_user = serializer.save()
            
            messages.success(request, f'ইউজার সফলভাবে তৈরি হয়েছে: {new_user.email}')
            return redirect('finance:dashboard')
        else:
            messages.error(request, f'ইউজার তৈরিতে সমস্যা: {serializer.errors}')
    
    # For GET request, show user creation form
    return render(request, 'finance/create_user.html', {'user': user})

@require_POST
@login_required
def update_profile(request):
    """Update User Profile"""
    user = request.user
    
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
