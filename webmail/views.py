from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q

from .models import EmailAccount, Email, EmailAttachment, Contact, EmailLabel
from .services import EmailService


def webmail_login(request):
    """Custom login view for webmail"""
    if request.user.is_authenticated:
        return redirect('webmail:inbox')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next', 'webmail:inbox')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            messages.success(request, 'Welcome to Webmail!')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email/username or password.')
    
    next_url = request.GET.get('next', 'webmail:inbox')
    return render(request, 'webmail/login.html', {'next': next_url})


@login_required(login_url='/webmail/login/')
def inbox(request):
    """Inbox view - main webmail interface"""
    # Get user's default email account
    try:
        account = EmailAccount.objects.filter(user=request.user, is_active=True).first()
        if not account:
            messages.warning(request, 'Please configure your email account first.')
            return redirect('webmail:account_setup')
    except EmailAccount.DoesNotExist:
        messages.warning(request, 'Please configure your email account first.')
        return redirect('webmail:account_setup')
    
    # Get folder from query params
    folder = request.GET.get('folder', 'inbox')
    
    # Get emails
    emails = Email.objects.filter(
        account=account,
        folder=folder
    ).order_by('-received_at')
    
    # Pagination
    paginator = Paginator(emails, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unread count
    unread_count = Email.objects.filter(account=account, folder='inbox', is_read=False).count()
    
    context = {
        'account': account,
        'emails': page_obj,
        'folder': folder,
        'unread_count': unread_count,
    }
    
    return render(request, 'webmail/inbox.html', context)


@login_required
def email_detail(request, email_id):
    """View single email"""
    account = EmailAccount.objects.filter(user=request.user, is_active=True).first()
    email = get_object_or_404(Email, id=email_id, account=account)
    
    # Mark as read
    if not email.is_read:
        email.mark_as_read()
    
    context = {
        'account': account,
        'email': email,
    }
    
    return render(request, 'webmail/email_detail.html', context)


@login_required
def compose(request):
    """Compose new email"""
    account = EmailAccount.objects.filter(user=request.user, is_active=True).first()
    
    if request.method == 'POST':
        to_addresses = request.POST.get('to', '').split(',')
        to_addresses = [email.strip() for email in to_addresses if email.strip()]
        
        cc_addresses = request.POST.get('cc', '').split(',')
        cc_addresses = [email.strip() for email in cc_addresses if email.strip()]
        
        subject = request.POST.get('subject', '')
        body_text = request.POST.get('body_text', '')
        body_html = request.POST.get('body_html', '')
        
        # Get attachments
        attachments = request.FILES.getlist('attachments')
        
        # Send email
        email_service = EmailService(account)
        
        if 'save_draft' in request.POST:
            result = email_service.save_draft(
                to_addresses=to_addresses,
                subject=subject,
                body_text=body_text,
                body_html=body_html
            )
            if result['success']:
                messages.success(request, 'Draft saved successfully!')
                return redirect('webmail:inbox')
        else:
            result = email_service.send_email(
                to_addresses=to_addresses,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                cc_addresses=cc_addresses if cc_addresses else None,
                attachments=attachments if attachments else None
            )
            
            if result['success']:
                messages.success(request, 'Email sent successfully!')
                return redirect('webmail:inbox')
            else:
                messages.error(request, f'Failed to send email: {result.get("error")}')
    
    context = {
        'account': account,
    }
    
    return render(request, 'webmail/compose.html', context)


@login_required
def account_setup(request):
    """Setup email account"""
    account = EmailAccount.objects.filter(user=request.user).first()
    
    if request.method == 'POST':
        email_address = request.POST.get('email_address')
        display_name = request.POST.get('display_name')
        aws_access_key = request.POST.get('aws_access_key')
        aws_secret_key = request.POST.get('aws_secret_key')
        aws_region = request.POST.get('aws_region', 'us-east-1')
        s3_bucket_name = request.POST.get('s3_bucket_name')
        
        if account:
            # Update existing account
            account.email_address = email_address
            account.display_name = display_name
            account.aws_access_key = aws_access_key
            account.aws_secret_key = aws_secret_key
            account.aws_region = aws_region
            account.s3_bucket_name = s3_bucket_name
            account.save()
            messages.success(request, 'Email account updated successfully!')
        else:
            # Create new account
            account = EmailAccount.objects.create(
                user=request.user,
                email_address=email_address,
                display_name=display_name,
                aws_access_key=aws_access_key,
                aws_secret_key=aws_secret_key,
                aws_region=aws_region,
                s3_bucket_name=s3_bucket_name,
                is_default=True,
                is_active=True
            )
            messages.success(request, 'Email account created successfully!')
        
        return redirect('webmail:inbox')
    
    context = {
        'account': account,
    }
    
    return render(request, 'webmail/account_setup.html', context)


@login_required
def delete_email(request, email_id):
    """Delete email (move to trash)"""
    account = EmailAccount.objects.filter(user=request.user, is_active=True).first()
    email = get_object_or_404(Email, id=email_id, account=account)
    
    email_service = EmailService(account)
    result = email_service.delete_email(email, permanent=False)
    
    if result['success']:
        messages.success(request, 'Email moved to trash.')
    else:
        messages.error(request, 'Failed to delete email.')
    
    return redirect('webmail:inbox')


@login_required
def search_emails(request):
    """Search emails"""
    account = EmailAccount.objects.filter(user=request.user, is_active=True).first()
    query = request.GET.get('q', '')
    
    if query:
        emails = Email.objects.filter(
            account=account
        ).filter(
            Q(subject__icontains=query) |
            Q(from_address__icontains=query) |
            Q(body_text__icontains=query)
        ).order_by('-received_at')
    else:
        emails = Email.objects.none()
    
    # Pagination
    paginator = Paginator(emails, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'account': account,
        'emails': page_obj,
        'query': query,
    }
    
    return render(request, 'webmail/search_results.html', context)


@login_required
def contacts(request):
    """View contacts"""
    contacts = Contact.objects.filter(user=request.user).order_by('-is_favorite', 'name')
    
    context = {
        'contacts': contacts,
    }
    
    return render(request, 'webmail/contacts.html', context)
