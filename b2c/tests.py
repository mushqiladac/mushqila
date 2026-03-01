"""
B2C Tests
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Customer, CustomerProfile

User = get_user_model()


class CustomerModelTest(TestCase):
    """Test Customer model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testcustomer',
            email='customer@test.com',
            password='testpass123'
        )
    
    def test_create_customer(self):
        """Test creating a customer"""
        customer = Customer.objects.create(
            user=self.user,
            customer_type='individual',
            loyalty_tier='bronze'
        )
        
        self.assertEqual(customer.user, self.user)
        self.assertEqual(customer.loyalty_tier, 'bronze')
        self.assertEqual(customer.loyalty_points, 0)
    
    def test_customer_str(self):
        """Test customer string representation"""
        customer = Customer.objects.create(
            user=self.user,
            loyalty_tier='gold'
        )
        
        expected = f"{self.user.get_full_name()} (gold)"
        self.assertEqual(str(customer), expected)


class CustomerProfileTest(TestCase):
    """Test CustomerProfile model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testcustomer',
            email='customer@test.com',
            password='testpass123'
        )
        self.customer = Customer.objects.create(user=self.user)
    
    def test_create_profile(self):
        """Test creating a customer profile"""
        profile = CustomerProfile.objects.create(
            customer=self.customer,
            gender='male',
            nationality='Bangladesh'
        )
        
        self.assertEqual(profile.customer, self.customer)
        self.assertEqual(profile.nationality, 'Bangladesh')
