from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Airline, Payment, PaymentAllocation, Sale


User = get_user_model()


class AccountingApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="TestPass123!",
            first_name="Admin",
            last_name="User",
            phone="+966512345678",
            user_type="admin",
            status="active",
        )
        self.user = User.objects.create_user(
            email="agent@example.com",
            password="TestPass123!",
            first_name="Agent",
            last_name="User",
            phone="+966512345679",
            user_type="agent",
            status="active",
        )
        self.airline = Airline.objects.create(code="EK", name="Emirates")

    def test_auth_me(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("accounting_api:auth_me"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])
        self.assertEqual(resp.data["data"]["email"], "agent@example.com")

    def test_non_admin_cannot_create_airline(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(reverse("accounting_api:airline-list"), {"code": "QR", "name": "Qatar"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_sees_own_sales_only(self):
        Sale.objects.create(
            airline=self.airline,
            user=self.user,
            pnr="PNR1",
            ticket_number="1760000000001",
            issue_date="2026-04-29",
            passenger_name="One",
            base_fare="100.00",
            customer_price="120.00",
            airline_cost="110.00",
        )
        Sale.objects.create(
            airline=self.airline,
            user=self.admin,
            pnr="PNR2",
            ticket_number="1760000000002",
            issue_date="2026-04-29",
            passenger_name="Two",
            base_fare="100.00",
            customer_price="120.00",
            airline_cost="110.00",
        )
        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("accounting_api:sale-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["results"]), 1)

    def test_outstanding_summary(self):
        sale = Sale.objects.create(
            airline=self.airline,
            user=self.user,
            pnr="PNR3",
            ticket_number="1760000000003",
            issue_date="2026-04-29",
            passenger_name="Three",
            base_fare="100.00",
            customer_price="150.00",
            airline_cost="120.00",
        )
        payment = Payment.objects.create(
            user=self.user,
            airline=self.airline,
            received_date="2026-04-29",
            amount="50.00",
            payment_method="cash",
        )
        PaymentAllocation.objects.create(payment=payment, sale=sale, amount="50.00")
        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("accounting_api:outstanding_summary"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["data"]["total_sales"], "150.00")
        self.assertEqual(resp.data["data"]["total_collection"], "50.00")
