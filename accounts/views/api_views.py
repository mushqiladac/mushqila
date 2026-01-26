"""
API views for B2B Travel Mushqila - Saudi Arabia
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

from ..models import User, FlightBooking, HotelBooking, Transaction, Payment
from ..serializers import (
    UserSerializer, FlightBookingSerializer, HotelBookingSerializer,
    TransactionSerializer, PaymentSerializer
)


class UserAPIView(APIView):
    """User API view"""
    
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.user_type != User.UserType.ADMIN:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        if request.user.user_type != User.UserType.ADMIN:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailAPIView(APIView):
    """User detail API view"""
    
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            
            # Check permissions
            if request.user.user_type != User.UserType.ADMIN and request.user != user:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = UserSerializer(user)
            return Response(serializer.data)
        
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class BookingAPIView(APIView):
    """Booking API view"""
    
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get user's bookings
        flights = FlightBooking.objects.filter(agent=request.user)
        hotels = HotelBooking.objects.filter(agent=request.user)
        
        flight_serializer = FlightBookingSerializer(flights, many=True)
        hotel_serializer = HotelBookingSerializer(hotels, many=True)
        
        return Response({
            'flights': flight_serializer.data,
            'hotels': hotel_serializer.data
        })


class BookingDetailAPIView(APIView):
    """Booking detail API view"""
    
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, booking_id):
        # Try to find in flights
        try:
            booking = FlightBooking.objects.get(booking_id=booking_id, agent=request.user)
            serializer = FlightBookingSerializer(booking)
            return Response(serializer.data)
        
        except FlightBooking.DoesNotExist:
            pass
        
        # Try to find in hotels
        try:
            booking = HotelBooking.objects.get(booking_id=booking_id, agent=request.user)
            serializer = HotelBookingSerializer(booking)
            return Response(serializer.data)
        
        except HotelBooking.DoesNotExist:
            pass
        
        return Response(
            {'error': 'Booking not found'},
            status=status.HTTP_404_NOT_FOUND
        )


class PaymentAPIView(APIView):
    """Payment API view"""
    
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        payments = Payment.objects.filter(user=request.user)
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            payment = serializer.save(user=request.user)
            return Response(
                PaymentSerializer(payment).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionAPIView(APIView):
    """Transaction API view"""
    
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        transactions = Transaction.objects.filter(user=request.user)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class WalletBalanceAPIView(APIView):
    """Wallet balance API view"""
    
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            'wallet_balance': float(user.wallet_balance),
            'credit_limit': float(user.credit_limit),
            'available_credit': float(user.available_credit()),
            'currency': 'SAR'
        })


# AJAX Views for dashboard components

class GetCitiesView(APIView):
    """Get cities by region (AJAX)"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        region_id = request.GET.get('region_id')
        
        from ..models import SaudiCity
        cities = SaudiCity.objects.filter(
            region_id=region_id,
            is_active=True
        ).values('id', 'name_en', 'name_ar')
        
        return Response(list(cities))


class AjaxFlightSearchView(APIView):
    """AJAX flight search"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # This would typically call an external API
        # For now, return mock data
        
        departure = request.GET.get('departure')
        destination = request.GET.get('destination')
        date = request.GET.get('date')
        
        flights = [
            {
                'airline': 'Saudia',
                'flight_number': 'SV 123',
                'departure': departure,
                'arrival': destination,
                'departure_time': '08:00',
                'arrival_time': '10:00',
                'price': 450.00,
                'currency': 'SAR'
            }
        ]
        
        return Response({'flights': flights})


class AjaxHotelSearchView(APIView):
    """AJAX hotel search"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # This would typically call an external API
        # For now, return mock data
        
        location = request.GET.get('location')
        check_in = request.GET.get('check_in')
        check_out = request.GET.get('check_out')
        
        hotels = [
            {
                'name': 'Hotel Example',
                'location': location,
                'check_in': check_in,
                'check_out': check_out,
                'price': 300.00,
                'currency': 'SAR'
            }
        ]
        
        return Response({'hotels': hotels})


class AjaxBookingStatusView(APIView):
    """AJAX booking status check"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, booking_id):
        from ..models import FlightBooking, HotelBooking
        
        # Check flights
        try:
            booking = FlightBooking.objects.get(
                booking_id=booking_id,
                agent=request.user
            )
            return Response({
                'status': booking.status,
                'type': 'flight',
                'details': FlightBookingSerializer(booking).data
            })
        except FlightBooking.DoesNotExist:
            pass
        
        # Check hotels
        try:
            booking = HotelBooking.objects.get(
                booking_id=booking_id,
                agent=request.user
            )
            return Response({
                'status': booking.status,
                'type': 'hotel',
                'details': HotelBookingSerializer(booking).data
            })
        except HotelBooking.DoesNotExist:
            pass
        
        return Response(
            {'error': 'Booking not found'},
            status=status.HTTP_404_NOT_FOUND
        )


class AjaxWalletBalanceView(APIView):
    """AJAX wallet balance check"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            'balance': float(user.wallet_balance),
            'formatted': f'{user.wallet_balance:,.2f} SAR'
        })