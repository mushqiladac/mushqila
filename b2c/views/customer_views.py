"""
B2C Customer Views
"""
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from b2c.models import Customer


class CustomerDashboardView(LoginRequiredMixin, TemplateView):
    """Customer Dashboard"""
    template_name = 'b2c/dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user is a customer
        if not hasattr(request.user, 'b2c_customer'):
            return redirect('b2c:register')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.request.user.b2c_customer
        
        context.update({
            'customer': customer,
            'loyalty_points': customer.loyalty_points,
            'total_bookings': customer.total_bookings,
            'loyalty_tier': customer.loyalty_tier,
        })
        return context


class CustomerProfileView(LoginRequiredMixin, TemplateView):
    """Customer Profile"""
    template_name = 'b2c/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.request.user.b2c_customer
        
        context.update({
            'customer': customer,
            'profile': getattr(customer, 'profile', None),
            'companions': customer.companions.all(),
        })
        return context


class CustomerBookingsView(LoginRequiredMixin, ListView):
    """Customer Bookings List"""
    template_name = 'b2c/bookings.html'
    context_object_name = 'bookings'
    paginate_by = 10
    
    def get_queryset(self):
        return self.request.user.bookings.all().order_by('-created_at')
