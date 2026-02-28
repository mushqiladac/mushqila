"""
Home views for Mushqila B2B Travel Platform
Production Ready - Landing Page and Home Views
"""

from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.http import Http404
import logging

logger = logging.getLogger(__name__)


class LandingPageView(TemplateView):
    """
    Public Landing Page - Main home page for non-logged in users
    This is the entry point of the website
    """
    template_name = 'accounts/landing.html'
    
    def dispatch(self, request, *args, **kwargs):
        """If user is already logged in, redirect to appropriate dashboard"""
        if request.user.is_authenticated:
            return redirect('accounts:dashboard_redirect')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Mushqila B2B Travel - Book Flights, Hotels, Hajj & Umrah',
            'meta_description': 'Premium B2B travel platform for agents. Book flights, hotels, Hajj packages, Umrah packages, and visa services with competitive rates.',
            'meta_keywords': 'travel, flights, hotels, hajj, umrah, visa, saudi arabia, travel agent, b2b',
            'show_navbar': True,
            'is_landing_page': True,
        })
        return context


class Landing2PageView(TemplateView):
    """
    Alternative Landing Page - Landing2 for testing and modifications
    """
    template_name = 'accounts/landing2.html'
    
    def dispatch(self, request, *args, **kwargs):
        """If user is already logged in, redirect to appropriate dashboard"""
        if request.user.is_authenticated:
            return redirect('accounts:dashboard_redirect')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Mushqila B2B Travel - Book Flights, Hotels, Hajj & Umrah',
            'meta_description': 'Premium B2B travel platform for agents. Book flights, hotels, Hajj packages, Umrah packages, and visa services with competitive rates.',
            'meta_keywords': 'travel, flights, hotels, hajj, umrah, visa, saudi arabia, travel agent, b2b',
            'show_navbar': True,
            'is_landing_page': True,
        })
        return context


class HomeView(TemplateView):
    """
    Home Page for logged-in users (Dashboard redirect)
    This view redirects users to their respective dashboards
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect to appropriate dashboard based on user type"""
        if not request.user.is_authenticated:
            # If not logged in, show landing page
            return redirect('accounts:landing')
        
        # Import dashboard redirect function
        from .dashboard_views import dashboard_redirect
        
        return dashboard_redirect(request)


class DashboardRedirectView(LoginRequiredMixin, TemplateView):
    """
    Dashboard Redirect View - Same as HomeView but with login required
    """
    template_name = 'accounts/dashboard/dashboard_redirect.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Redirect to appropriate dashboard"""
        from .dashboard_views import dashboard_redirect
        return dashboard_redirect(request)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Redirecting to Dashboard')
        return context


class CookiesPolicyView(TemplateView):
    """Cookies Policy Page"""
    template_name = 'accounts/cookies.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Cookies Policy - Mushqila Travel',
            'meta_description': 'Cookies policy and privacy information for Mushqila B2B Travel Platform.',
        })
        return context


class PrivacyPolicyView(TemplateView):
    """Privacy Policy Page"""
    template_name = 'accounts/privacy_policy.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Privacy Policy - Mushqila Travel',
            'meta_description': 'Privacy policy for Mushqila B2B Travel Platform.',
        })
        return context


class TermsOfServiceView(TemplateView):
    """Terms of Service Page"""
    template_name = 'accounts/terms_of_service.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Terms of Service - Mushqila Travel',
            'meta_description': 'Terms of service for Mushqila B2B Travel Platform.',
        })
        return context


class AboutUsView(TemplateView):
    """About Us Page"""
    template_name = 'accounts/about_us.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'About Us - Mushqila Travel',
            'meta_description': 'Learn about Mushqila B2B Travel Platform and our services.',
        })
        return context


class ContactUsView(TemplateView):
    """Contact Us Page"""
    template_name = 'accounts/contact_us.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Contact Us - Mushqila Travel',
            'meta_description': 'Contact Mushqila B2B Travel Platform for inquiries and support.',
        })
        return context


class FAQView(TemplateView):
    """FAQ Page"""
    template_name = 'accounts/faq.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Sample FAQ data
        faqs = [
            {
                'question': 'How do I register as an agent?',
                'answer': 'Click on the "Become an Agent" button on the landing page and fill out the registration form.',
            },
            {
                'question': 'What documents are required for KYC?',
                'answer': 'You need to provide your national ID, trade license, and proof of address documents.',
            },
            {
                'question': 'How long does it take to get approved?',
                'answer': 'Approval typically takes 24-48 hours after submitting all required documents.',
            },
            {
                'question': 'What commission rates do you offer?',
                'answer': 'Commission rates vary based on services and volume. Contact our sales team for details.',
            },
            {
                'question': 'How do I make payments?',
                'answer': 'Payments can be made through bank transfer, credit card, or digital wallets.',
            },
        ]
        
        context.update({
            'page_title': 'Frequently Asked Questions - Mushqila Travel',
            'meta_description': 'Find answers to common questions about Mushqila B2B Travel Platform.',
            'faqs': faqs,
        })
        return context


class ServicesView(TemplateView):
    """Services Overview Page"""
    template_name = 'accounts/services.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        services = [
            {
                'title': 'Flight Bookings',
                'icon': 'fas fa-plane',
                'description': 'Domestic and international flights with competitive rates and flexible options.',
                'features': ['One-way, round-trip, multi-city', 'Instant confirmation', 'Competitive pricing'],
            },
            {
                'title': 'Hotel Reservations',
                'icon': 'fas fa-hotel',
                'description': 'Premium hotels worldwide with exclusive rates and special packages.',
                'features': ['5-star to budget hotels', 'Free cancellation options', 'Breakfast included'],
            },
            {
                'title': 'Hajj Packages',
                'icon': 'fas fa-kaaba',
                'description': 'Complete Hajj packages with accommodation, transport, and guidance services.',
                'features': ['Certified packages', 'Medical support', 'Near Haram accommodation'],
            },
            {
                'title': 'Umrah Packages',
                'icon': 'fas fa-mosque',
                'description': 'Year-round Umrah packages with visa processing and comprehensive support.',
                'features': ['Flexible dates', 'Group discounts', 'Visa assistance'],
            },
            {
                'title': 'Visa Services',
                'icon': 'fas fa-passport',
                'description': 'Saudi visa, Umrah visa, business visa, and tourist visa processing.',
                'features': ['Fast processing', 'Document assistance', 'Guaranteed approval'],
            },
            {
                'title': 'Transport & Tours',
                'icon': 'fas fa-car',
                'description': 'Airport transfers, city tours, and intercity transport services.',
                'features': ['24/7 service', 'English speaking drivers', 'Professional guides'],
            },
        ]
        
        context.update({
            'page_title': 'Our Services - Mushqila Travel',
            'meta_description': 'Comprehensive travel services including flights, hotels, Hajj, Umrah, and visa processing.',
            'services': services,
        })
        return context


class Error404View(TemplateView):
    """Custom 404 Error Page"""
    template_name = 'accounts/errors/404.html'
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context, status=404)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Page Not Found - Mushqila Travel',
            'error_code': 404,
            'error_message': 'The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.',
        })
        return context


class Error403View(TemplateView):
    """Custom 403 Error Page"""
    template_name = 'accounts/errors/403.html'
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context, status=403)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Access Denied - Mushqila Travel',
            'error_code': 403,
            'error_message': 'You do not have permission to access this page.',
        })
        return context


class Error500View(TemplateView):
    """Custom 500 Error Page"""
    template_name = 'accounts/errors/500.html'
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context, status=500)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Server Error - Mushqila Travel',
            'error_code': 500,
            'error_message': 'An internal server error has occurred. Please try again later.',
        })
        return context


# Error handler functions for Django
def handler404(request, exception):
    view = Error404View()
    return view.get(request)


def handler403(request, exception):
    view = Error403View()
    return view.get(request)


def handler500(request):
    view = Error500View()
    return view.get(request)