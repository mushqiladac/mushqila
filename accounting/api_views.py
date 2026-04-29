from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Q, Sum
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Airline, AuditLog, Payment, PaymentAllocation, Sale
from .permissions import IsAdminForWriteElseReadOnly, IsOwnerOrAdminObject, IsSuperUserOrAdminType
from .serializers import (
    AirlineSerializer,
    AuditLogSerializer,
    PaymentAllocationSerializer,
    PaymentSerializer,
    SaleSerializer,
)


User = get_user_model()


def success_response(data=None, message="Request successful", meta=None, status_code=status.HTTP_200_OK):
    return Response(
        {
            "success": True,
            "message": message,
            "data": data,
            "errors": None,
            "meta": meta or {},
        },
        status=status_code,
    )


def error_response(message="Request failed", errors=None, code="REQUEST_FAILED", status_code=status.HTTP_400_BAD_REQUEST):
    return Response(
        {
            "success": False,
            "message": message,
            "data": None,
            "errors": errors or {},
            "code": code,
        },
        status=status_code,
    )


def is_admin_user(user):
    return user.is_superuser or user.user_type == "admin"


def create_audit_log(request, action, entity, entity_id, description="", metadata=None):
    AuditLog.objects.create(
        actor=request.user if request.user.is_authenticated else None,
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        description=description,
        metadata=metadata or {},
        ip_address=request.META.get("REMOTE_ADDR"),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:1000],
    )


class AccountingTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.user_type
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,
            "name": self.user.get_full_name() or self.user.username,
            "email": self.user.email,
            "role": self.user.user_type,
        }
        return data


class AccountingLoginView(TokenObtainPairView):
    serializer_class = AccountingTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code >= 400:
            return error_response(message="Invalid credentials", errors=response.data, code="AUTH_INVALID")
        return success_response(data=response.data, message="Login successful")


class AirlineViewSet(viewsets.ModelViewSet):
    queryset = Airline.objects.all()
    serializer_class = AirlineSerializer
    permission_classes = [IsAdminForWriteElseReadOnly]

    def perform_create(self, serializer):
        obj = serializer.save()
        create_audit_log(self.request, "create", "airline", obj.id, f"Airline {obj.code} created")

    def perform_update(self, serializer):
        obj = serializer.save()
        create_audit_log(self.request, "update", "airline", obj.id, f"Airline {obj.code} updated")


class SaleViewSet(viewsets.ModelViewSet):
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Sale.objects.select_related("airline", "user").all()
        user = self.request.user
        params = self.request.query_params

        if not (user.is_superuser or user.user_type == "admin"):
            queryset = queryset.filter(user=user)

        if params.get("from_date"):
            queryset = queryset.filter(issue_date__gte=params["from_date"])
        if params.get("to_date"):
            queryset = queryset.filter(issue_date__lte=params["to_date"])
        if params.get("airline_id"):
            queryset = queryset.filter(airline_id=params["airline_id"])
        if params.get("user_id") and (user.is_superuser or user.user_type == "admin"):
            queryset = queryset.filter(user_id=params["user_id"])
        if params.get("status"):
            queryset = queryset.filter(status=params["status"])
        if params.get("search"):
            search = params["search"]
            queryset = queryset.filter(
                Q(pnr__icontains=search)
                | Q(ticket_number__icontains=search)
                | Q(passenger_name__icontains=search)
            )
        return queryset

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [IsOwnerOrAdminObject()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        requested_user_id = self.request.data.get("user")
        if is_admin_user(user) and requested_user_id:
            assigned_user = User.objects.filter(id=requested_user_id).first() or user
        else:
            assigned_user = user
        obj = serializer.save(user=assigned_user)
        create_audit_log(self.request, "create", "sale", obj.id, f"Sale created for ticket {obj.ticket_number}")

    def perform_update(self, serializer):
        obj = serializer.save()
        create_audit_log(self.request, "update", "sale", obj.id, f"Sale updated for ticket {obj.ticket_number}")

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        sale = self.get_object()
        sale.status = Sale.SaleStatus.VOID
        sale.save(update_fields=["status", "updated_at"])
        create_audit_log(request, "status_change", "sale", sale.id, "Sale marked as void")
        return success_response(data=SaleSerializer(sale).data, message="Sale marked as void")

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        sale = self.get_object()
        sale.status = Sale.SaleStatus.REFUND
        sale.save(update_fields=["status", "updated_at"])
        create_audit_log(request, "status_change", "sale", sale.id, "Sale marked as refund")
        return success_response(data=SaleSerializer(sale).data, message="Sale marked as refund")

    @action(detail=True, methods=["post"])
    def reissue(self, request, pk=None):
        sale = self.get_object()
        sale.status = Sale.SaleStatus.REISSUE
        sale.save(update_fields=["status", "updated_at"])
        create_audit_log(request, "status_change", "sale", sale.id, "Sale marked as reissue")
        return success_response(data=SaleSerializer(sale).data, message="Sale marked as reissue")


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Payment.objects.select_related("airline", "user").all()
        user = self.request.user
        if not (user.is_superuser or user.user_type == "admin"):
            queryset = queryset.filter(user=user)
        return queryset

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [IsOwnerOrAdminObject()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        requested_user_id = self.request.data.get("user")
        if is_admin_user(user) and requested_user_id:
            assigned_user = User.objects.filter(id=requested_user_id).first() or user
        else:
            assigned_user = user
        obj = serializer.save(user=assigned_user)
        create_audit_log(self.request, "create", "payment", obj.id, f"Payment created amount {obj.amount}")

    def perform_update(self, serializer):
        obj = serializer.save()
        create_audit_log(self.request, "update", "payment", obj.id, f"Payment updated amount {obj.amount}")


class PaymentAllocationViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentAllocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = PaymentAllocation.objects.select_related("payment", "sale", "payment__user")
        user = self.request.user
        if not is_admin_user(user):
            queryset = queryset.filter(payment__user=user)
        return queryset

    def perform_create(self, serializer):
        obj = serializer.save()
        create_audit_log(self.request, "create", "payment_allocation", obj.id, f"Allocation {obj.amount} created")


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def outstanding_summary_view(request):
    user = request.user
    sales = Sale.objects.all()
    if not (user.is_superuser or user.user_type == "admin"):
        sales = sales.filter(user=user)

    total_sales = sales.aggregate(total=Sum("customer_price"))["total"] or Decimal("0.00")
    total_allocated = (
        PaymentAllocation.objects.filter(sale__in=sales).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )
    outstanding = total_sales - total_allocated

    data = {
        "total_sales": f"{total_sales:.2f}",
        "total_collection": f"{total_allocated:.2f}",
        "total_outstanding": f"{outstanding:.2f}",
    }
    return success_response(data=data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated, IsSuperUserOrAdminType])
def dashboard_super_view(request):
    sales_total = Sale.objects.aggregate(total=Sum("customer_price"))["total"] or Decimal("0.00")
    collection_total = Payment.objects.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    data = {
        "total_sales": f"{sales_total:.2f}",
        "total_collection": f"{collection_total:.2f}",
        "outstanding": f"{(sales_total - collection_total):.2f}",
        "sales_count": Sale.objects.count(),
    }
    return success_response(data=data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def dashboard_user_view(request):
    sales = Sale.objects.filter(user=request.user)
    payments = Payment.objects.filter(user=request.user)
    sales_total = sales.aggregate(total=Sum("customer_price"))["total"] or Decimal("0.00")
    collection_total = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    data = {
        "my_sales": f"{sales_total:.2f}",
        "my_collection": f"{collection_total:.2f}",
        "my_outstanding": f"{(sales_total - collection_total):.2f}",
        "my_sales_count": sales.count(),
    }
    return success_response(data=data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def report_sales_view(request):
    user = request.user
    qs = Sale.objects.select_related("airline", "user")
    if not is_admin_user(user):
        qs = qs.filter(user=user)

    from_date = request.query_params.get("from_date")
    to_date = request.query_params.get("to_date")
    airline_id = request.query_params.get("airline_id")
    user_id = request.query_params.get("user_id")

    if from_date:
        qs = qs.filter(issue_date__gte=from_date)
    if to_date:
        qs = qs.filter(issue_date__lte=to_date)
    if airline_id:
        qs = qs.filter(airline_id=airline_id)
    if user_id and is_admin_user(user):
        qs = qs.filter(user_id=user_id)

    totals = qs.aggregate(
        total_sales=Sum("customer_price"),
        total_airline_cost=Sum("airline_cost"),
        total_commission=Sum("commission_amount"),
    )
    data = {
        "summary": {
            "total_sales": f"{(totals['total_sales'] or Decimal('0.00')):.2f}",
            "total_airline_cost": f"{(totals['total_airline_cost'] or Decimal('0.00')):.2f}",
            "total_commission": f"{(totals['total_commission'] or Decimal('0.00')):.2f}",
            "count": qs.count(),
        },
        "items": SaleSerializer(qs[:200], many=True).data,
    }
    return success_response(data=data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated, IsSuperUserOrAdminType])
def audit_logs_view(request):
    logs = AuditLog.objects.select_related("actor").all()[:300]
    return success_response(data=AuditLogSerializer(logs, many=True).data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def auth_me_view(request):
    user = request.user
    data = {
        "id": user.id,
        "name": user.get_full_name() or user.username,
        "email": user.email,
        "role": getattr(user, "user_type", None),
        "is_superuser": user.is_superuser,
    }
    return success_response(data=data)
