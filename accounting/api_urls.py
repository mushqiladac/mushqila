from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .api_views import (
    AirlineViewSet,
    AccountingLoginView,
    PaymentAllocationViewSet,
    PaymentViewSet,
    SaleViewSet,
    audit_logs_view,
    auth_me_view,
    dashboard_super_view,
    dashboard_user_view,
    outstanding_summary_view,
    report_sales_view,
)

app_name = "accounting_api"

router = DefaultRouter()
router.register(r"airlines", AirlineViewSet, basename="airline")
router.register(r"sales", SaleViewSet, basename="sale")
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"payment-allocations", PaymentAllocationViewSet, basename="payment-allocation")

urlpatterns = [
    path("auth/login/", AccountingLoginView.as_view(), name="auth_login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", auth_me_view, name="auth_me"),
    path("outstanding/summary/", outstanding_summary_view, name="outstanding_summary"),
    path("dashboard/super/", dashboard_super_view, name="dashboard_super"),
    path("dashboard/user/", dashboard_user_view, name="dashboard_user"),
    path("reports/sales/", report_sales_view, name="report_sales"),
    path("audit/logs/", audit_logs_view, name="audit_logs"),
    path("", include(router.urls)),
]
