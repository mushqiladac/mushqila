"""B2C Loyalty Views - Placeholder"""
from django.views.generic import TemplateView

class LoyaltyDashboardView(TemplateView):
    template_name = 'b2c/loyalty/dashboard.html'

class RewardsView(TemplateView):
    template_name = 'b2c/loyalty/rewards.html'

class RedeemRewardView(TemplateView):
    template_name = 'b2c/loyalty/redeem.html'
