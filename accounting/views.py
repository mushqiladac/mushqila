from decimal import Decimal
import csv
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.db.models.functions import TruncMonth

from .forms import PaymentAllocationForm, PaymentForm, SaleForm
from .models import Airline, Payment, Sale

User = get_user_model()


def _is_admin(user):
    return user.is_superuser or getattr(user, "user_type", "") == "admin"


@login_required
def dashboard_view(request):
    user = request.user
    sales = Sale.objects.select_related("airline", "user")
    payments = Payment.objects.select_related("airline", "user")

    if not _is_admin(user):
        sales = sales.filter(user=user)
        payments = payments.filter(user=user)

    total_sales = sales.aggregate(total=Sum("customer_price"))["total"] or Decimal("0.00")
    total_collection = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    outstanding = total_sales - total_collection
    today = date.today()
    aging_buckets = {"0_7": Decimal("0.00"), "8_15": Decimal("0.00"), "16_30": Decimal("0.00"), "31_plus": Decimal("0.00")}
    for sale in sales:
        due = sale.due_amount
        if due <= 0:
            continue
        age_days = max(0, (today - sale.issue_date).days)
        if age_days <= 7:
            aging_buckets["0_7"] += due
        elif age_days <= 15:
            aging_buckets["8_15"] += due
        elif age_days <= 30:
            aging_buckets["16_30"] += due
        else:
            aging_buckets["31_plus"] += due

    monthly_sales = (
        sales.annotate(month=TruncMonth("issue_date"))
        .values("month")
        .annotate(total=Sum("customer_price"))
        .order_by("month")[:12]
    )
    monthly_collection = (
        payments.annotate(month=TruncMonth("received_date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")[:12]
    )

    context = {
        "is_admin": _is_admin(user),
        "total_sales": total_sales,
        "total_collection": total_collection,
        "total_outstanding": outstanding,
        "sales_count": sales.count(),
        "payment_count": payments.count(),
        "recent_sales": sales.order_by("-created_at")[:8],
        "recent_payments": payments.order_by("-created_at")[:8],
        "sales_trend_labels": [item["month"].strftime("%b %Y") for item in monthly_sales if item["month"]],
        "sales_trend_values": [float(item["total"] or 0) for item in monthly_sales],
        "collection_trend_values": [float(item["total"] or 0) for item in monthly_collection],
        "aging_buckets": aging_buckets,
        "can_manage_accounting": _is_admin(user),
    }
    return render(request, "accounting/dashboard.html", context)


@login_required
def sales_list_view(request):
    user = request.user
    sales = Sale.objects.select_related("airline", "user").order_by("-issue_date", "-id")
    if not _is_admin(user):
        sales = sales.filter(user=user)
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    airline_id = request.GET.get("airline_id")
    status_value = request.GET.get("status")
    user_id = request.GET.get("user_id")

    if from_date:
        sales = sales.filter(issue_date__gte=from_date)
    if to_date:
        sales = sales.filter(issue_date__lte=to_date)
    if airline_id:
        sales = sales.filter(airline_id=airline_id)
    if status_value:
        sales = sales.filter(status=status_value)
    if user_id and _is_admin(user):
        sales = sales.filter(user_id=user_id)

    paginator = Paginator(sales, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "sales": page_obj.object_list,
        "page_obj": page_obj,
        "airlines": Airline.objects.filter(is_active=True).order_by("code"),
        "users": User.objects.order_by("email")[:200] if _is_admin(user) else [],
        "filters": request.GET,
        "can_manage_accounting": _is_admin(user),
    }
    return render(request, "accounting/sales_list.html", context)


@login_required
def outstanding_view(request):
    user = request.user
    sales = Sale.objects.select_related("airline", "user")
    if not _is_admin(user):
        sales = sales.filter(user=user)

    items = []
    total_due = Decimal("0.00")
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    if from_date:
        sales = sales.filter(issue_date__gte=from_date)
    if to_date:
        sales = sales.filter(issue_date__lte=to_date)

    for sale in sales.order_by("-issue_date"):
        due = sale.due_amount
        if due > 0:
            total_due += due
            items.append({"sale": sale, "due": due})

    paginator = Paginator(items, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "items": page_obj.object_list,
        "page_obj": page_obj,
        "total_due": total_due,
        "filters": request.GET,
        "can_manage_accounting": _is_admin(user),
    }
    return render(request, "accounting/outstanding.html", context)


@login_required
def reports_view(request):
    user = request.user
    sales = Sale.objects.all()
    payments = Payment.objects.all()
    if not _is_admin(user):
        sales = sales.filter(user=user)
        payments = payments.filter(user=user)

    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")
    if from_date:
        sales = sales.filter(issue_date__gte=from_date)
        payments = payments.filter(received_date__gte=from_date)
    if to_date:
        sales = sales.filter(issue_date__lte=to_date)
        payments = payments.filter(received_date__lte=to_date)

    summary = {
        "total_sales": sales.aggregate(total=Sum("customer_price"))["total"] or Decimal("0.00"),
        "total_commission": sales.aggregate(total=Sum("commission_amount"))["total"] or Decimal("0.00"),
        "total_airline_cost": sales.aggregate(total=Sum("airline_cost"))["total"] or Decimal("0.00"),
        "total_collection": payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
    }
    summary["profit_estimate"] = summary["total_sales"] - summary["total_airline_cost"]

    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="accounting-report.csv"'
        writer = csv.writer(response)
        writer.writerow(["Metric", "Amount"])
        writer.writerow(["Total Sales", summary["total_sales"]])
        writer.writerow(["Total Collection", summary["total_collection"]])
        writer.writerow(["Total Commission", summary["total_commission"]])
        writer.writerow(["Total Airline Cost", summary["total_airline_cost"]])
        writer.writerow(["Estimated Profit", summary["profit_estimate"]])
        return response

    monthly_sales = (
        sales.annotate(month=TruncMonth("issue_date"))
        .values("month")
        .annotate(total=Sum("customer_price"))
        .order_by("month")[:12]
    )
    monthly_collection = (
        payments.annotate(month=TruncMonth("received_date"))
        .values("month")
        .annotate(total=Sum("amount"))
        .order_by("month")[:12]
    )

    return render(
        request,
        "accounting/reports.html",
        {
            "summary": summary,
            "filters": request.GET,
            "trend_labels": [item["month"].strftime("%b %Y") for item in monthly_sales if item["month"]],
            "sales_values": [float(item["total"] or 0) for item in monthly_sales],
            "collection_values": [float(item["total"] or 0) for item in monthly_collection],
            "can_manage_accounting": _is_admin(user),
        },
    )


@login_required
def sale_create_view(request):
    form = SaleForm(request.POST or None)
    if not _is_admin(request.user):
        form.fields["user"].queryset = User.objects.filter(id=request.user.id)
        form.initial["user"] = request.user
    if request.method == "POST" and form.is_valid():
        if not _is_admin(request.user):
            form.instance.user = request.user
        form.save()
        messages.success(request, "Sale created successfully.")
        return redirect("accounting:sales_list")
    if request.method == "POST":
        messages.error(request, "Please correct the sale form errors.")
    return render(request, "accounting/sale_form.html", {"form": form, "title": "Create Sale"})


@login_required
def payment_create_view(request):
    form = PaymentForm(request.POST or None)
    if not _is_admin(request.user):
        form.fields["user"].queryset = User.objects.filter(id=request.user.id)
        form.initial["user"] = request.user
    if request.method == "POST" and form.is_valid():
        if not _is_admin(request.user):
            form.instance.user = request.user
        form.save()
        messages.success(request, "Payment created successfully.")
        return redirect("accounting:dashboard")
    if request.method == "POST":
        messages.error(request, "Please correct the payment form errors.")
    return render(request, "accounting/payment_form.html", {"form": form, "title": "Create Payment"})


@login_required
def allocation_create_view(request):
    form = PaymentAllocationForm(request.POST or None)
    if not _is_admin(request.user):
        form.fields["payment"].queryset = Payment.objects.filter(user=request.user)
        form.fields["sale"].queryset = Sale.objects.filter(user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Payment allocation created successfully.")
        return redirect("accounting:outstanding")
    if request.method == "POST":
        messages.error(request, "Please correct the allocation form errors.")
    return render(request, "accounting/allocation_form.html", {"form": form, "title": "Allocate Payment"})
