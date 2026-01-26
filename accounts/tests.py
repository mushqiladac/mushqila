"""
Tests for accounts app
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail

from .models import UserProfile, Transaction
from .forms import LoginForm, UserRegistrationForm

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model"""

    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '+966512345678',
            'password': 'testpass123'
        }

    def test_create_user(self):
        """Test user creation"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.get_full_name(), 'Test User')
        self.assertTrue(user.check_password(self.user_data['password']))

    def test_create_superuser(self):
        """Test superuser creation"""
        superuser = User.objects.create_superuser(**self.user_data)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_staff)
        self.assertEqual(superuser.user_type, User.UserType.ADMIN)

    def test_user_str(self):
        """Test user string representation"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'Test User (test@example.com)')


class UserProfileTest(TestCase):
    """Test UserProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            phone='+966512345678',
            password='testpass123'
        )

    def test_profile_creation(self):
        """Test that profile is created automatically"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)


class LoginFormTest(TestCase):
    """Test login form"""

    def test_valid_email_login(self):
        """Test login form with email"""
        form_data = {
            'login_type': 'email',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_valid_phone_login(self):
        """Test login form with phone"""
        form_data = {
            'login_type': 'phone',
            'phone': '+966512345678',
            'password': 'testpass123'
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())


class UserRegistrationFormTest(TestCase):
    """Test user registration form"""

    def test_valid_registration(self):
        """Test valid registration data"""
        form_data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'phone': '+966598765432',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'user_type': 'agent'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())


class AuthenticationTest(TestCase):
    """Test authentication views"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            phone='+966512345678',
            password='testpass123'
        )

    def test_login_view_get(self):
        """Test login view GET request"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/auth/login.html')

    def test_login_view_post_valid(self):
        """Test login view POST with valid credentials"""
        response = self.client.post(reverse('accounts:login'), {
            'login_type': 'email',
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login


class TemplateTagsTest(TestCase):
    """Test custom template tags"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            phone='+966512345678',
            password='testpass123',
            user_type='agent',
            status='active'
        )

    def test_user_type_display(self):
        """Test user_type_display filter"""
        from accounts.templatetags.custom_filters import user_type_display
        result = user_type_display('agent')
        self.assertEqual(str(result), 'Travel Agent')

    def test_status_display(self):
        """Test status_display filter"""
        from accounts.templatetags.custom_filters import status_display
        result = status_display('active')
        self.assertEqual(str(result), 'Active')

    def test_currency_format(self):
        """Test currency_format filter"""
        from accounts.templatetags.custom_filters import currency_format
        result = currency_format(1234.56)
        self.assertEqual(result, '1,234.56')
