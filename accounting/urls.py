from django.urls import path

from . import views

app_name = "accounting"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("sales/", views.sales_list_view, name="sales_list"),
    path("sales/create/", views.sale_create_view, name="sale_create"),
    path("payments/create/", views.payment_create_view, name="payment_create"),
    path("allocations/create/", views.allocation_create_view, name="allocation_create"),
    path("outstanding/", views.outstanding_view, name="outstanding"),
    path("reports/", views.reports_view, name="reports"),
]
