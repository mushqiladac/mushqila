from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from finance.models import Airline, PaymentMethod, NotificationTemplate
from decimal import Decimal


class Command(BaseCommand):
    help = 'Setup initial data for finance app'
    
    def handle(self, *args, **options):
        self.stdout.write('Setting up finance app initial data...')
        
        # Create airlines
        self.create_airlines()
        
        # Create payment methods
        self.create_payment_methods()
        
        # Create notification templates
        self.create_notification_templates()
        
        # Create admin user
        self.create_admin_user()
        
        self.stdout.write(self.style.SUCCESS('Finance app setup completed successfully!'))
    
    def create_airlines(self):
        """Create default airlines"""
        airlines_data = [
            {'code': 'SV', 'name': 'Saudia Airlines', 'name_ar': 'الخطوط الجوية السعودية', 'country': 'Saudi Arabia'},
            {'code': 'FV', 'name': 'flyadeal', 'name_ar': 'فلاي عديل', 'country': 'Saudi Arabia'},
            {'code': 'XY', 'name': 'Flynas', 'name_ar': 'طيران ناس', 'country': 'Saudi Arabia'},
            {'code': 'EK', 'name': 'Emirates', 'name_ar': 'طيران الإمارات', 'country': 'UAE'},
            {'code': 'QR', 'name': 'Qatar Airways', 'name_ar': 'الطيران القطري', 'country': 'Qatar'},
            {'code': 'EY', 'name': 'Etihad Airways', 'name_ar': 'الاتحاد للطيران', 'country': 'UAE'},
            {'code': 'TK', 'name': 'Turkish Airlines', 'name_ar': 'الخطوط الجوية التركية', 'country': 'Turkey'},
            {'code': 'GF', 'name': 'Gulf Air', 'name_ar': 'طيران الخليج', 'country': 'Bahrain'},
            {'code': 'KU', 'name': 'Kuwait Airways', 'name_ar': 'طيران الكويت', 'country': 'Kuwait'},
            {'code': 'WY', 'name': 'Oman Air', 'name_ar': 'الطيران العماني', 'country': 'Oman'},
        ]
        
        created_count = 0
        for airline_data in airlines_data:
            airline, created = Airline.objects.get_or_create(
                code=airline_data['code'],
                defaults=airline_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'  Created airline: {airline.code} - {airline.name}')
        
        self.stdout.write(f'  Airlines created: {created_count}')
    
    def create_payment_methods(self):
        """Create default payment methods"""
        payment_methods_data = [
            {'name': 'bank', 'name_ar': 'تحويل بنكي', 'description': 'Bank transfer payment'},
            {'name': 'span', 'name_ar': 'سبان', 'description': 'SPAN payment system'},
            {'name': 'bkash', 'name_ar': 'بيكاش', 'description': 'bKash mobile payment'},
            {'name': 'nagad', 'name_ar': 'نقاد', 'description': 'Nagad mobile payment'},
            {'name': 'cash', 'name_ar': 'نقد', 'description': 'Cash payment'},
            {'name': 'card', 'name_ar': 'بطاقة', 'description': 'Credit/Debit card payment'},
            {'name': 'other', 'name_ar': 'أخرى', 'description': 'Other payment method'},
        ]
        
        created_count = 0
        for payment_data in payment_methods_data:
            payment_method, created = PaymentMethod.objects.get_or_create(
                name=payment_data['name'],
                defaults=payment_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'  Created payment method: {payment_method.get_name_display()}')
        
        self.stdout.write(f'  Payment methods created: {created_count}')
    
    def create_notification_templates(self):
        """Create default notification templates"""
        templates_data = [
            {
                'template_type': 'welcome_email',
                'subject': 'Welcome to Finance App',
                'subject_ar': 'مرحبا بك في تطبيق المالية',
                'html_content': '<h1>Welcome {{name}}!</h1><p>Thank you for joining Finance App. Your account has been created successfully.</p><p>Email: {{email}}</p><p>User Type: {{user_type}}</p>',
                'html_content_ar': '<h1>مرحبا {{name}}!</h1><p>شكرا لانضمامك إلى تطبيق المالية. تم إنشاء حسابك بنجاح.</p><p>البريد الإلكتروني: {{email}}</p><p>نوع المستخدم: {{user_type}}</p>',
                'text_content': 'Welcome {{name}}! Thank you for joining Finance App. Your account has been created successfully.',
                'text_content_ar': 'مرحبا {{name}}! شكرا لانضمامك إلى تطبيق المالية. تم إنشاء حسابك بنجاح.'
            },
            {
                'template_type': 'password_reset',
                'subject': 'Password Reset OTP',
                'subject_ar': 'OTP إعادة تعيين كلمة المرور',
                'html_content': '<h1>Password Reset</h1><p>Your OTP code is: <strong>{{otp_code}}</strong></p><p>This code will expire in 10 minutes.</p>',
                'html_content_ar': '<h1>إعادة تعيين كلمة المرور</h1><p>رمز OTP الخاص بك هو: <strong>{{otp_code}}</strong></p><p>هذا الرمز سينتهي صلاحيته في 10 دقائق.</p>',
                'text_content': 'Your OTP code is: {{otp_code}}. This code will expire in 10 minutes.',
                'text_content_ar': 'رمز OTP الخاص بك هو: {{otp_code}}. هذا الرمز سينتهي صلاحيته في 10 دقائق.'
            },
            {
                'template_type': 'ticket_approved',
                'subject': 'Ticket Sale Approved',
                'subject_ar': 'تمت الموافقة على بيع التذكرة',
                'html_content': '<h1>Ticket Approved</h1><p>Your ticket sale has been approved.</p><p><strong>Ticket Number:</strong> {{ticket_number}}</p><p><strong>Passenger:</strong> {{passenger_name}}</p><p><strong>Amount:</strong> {{amount}} SAR</p>',
                'html_content_ar': '<h1>تمت الموافقة على التذكرة</h1><p>تمت الموافقة على بيع تذكرتك.</p><p><strong>رقم التذكرة:</strong> {{ticket_number}}</p><p><strong>الراكب:</strong> {{passenger_name}}</p><p><strong>المبلغ:</strong> {{amount}} ريال</p>',
                'text_content': 'Your ticket sale has been approved. Ticket Number: {{ticket_number}}, Passenger: {{passenger_name}}, Amount: {{amount}} SAR',
                'text_content_ar': 'تمت الموافقة على بيع تذكرتك. رقم التذكرة: {{ticket_number}}، الراكب: {{passenger_name}}، المبلغ: {{amount}} ريال'
            },
            {
                'template_type': 'ticket_rejected',
                'subject': 'Ticket Sale Rejected',
                'subject_ar': 'تم رفض بيع التذكرة',
                'html_content': '<h1>Ticket Rejected</h1><p>Your ticket sale has been rejected.</p><p><strong>Ticket Number:</strong> {{ticket_number}}</p><p><strong>Reason:</strong> {{reason}}</p>',
                'html_content_ar': '<h1>تم رفض التذكرة</h1><p>تم رفض بيع تذكرتك.</p><p><strong>رقم التذكرة:</strong> {{ticket_number}}</p><p><strong>السبب:</strong> {{reason}}</p>',
                'text_content': 'Your ticket sale has been rejected. Ticket Number: {{ticket_number}}, Reason: {{reason}}',
                'text_content_ar': 'تم رفض بيع تذكرتك. رقم التذكرة: {{ticket_number}}، السبب: {{reason}}'
            },
            {
                'template_type': 'payment_received',
                'subject': 'Payment Received',
                'subject_ar': 'تم استلام الدفعة',
                'html_content': '<h1>Payment Received</h1><p>We have received your payment.</p><p><strong>Amount:</strong> {{amount}} SAR</p><p><strong>Ticket Number:</strong> {{ticket_number}}</p><p><strong>Remaining Balance:</strong> {{remaining_balance}} SAR</p>',
                'html_content_ar': '<h1>تم استلام الدفعة</h1><p>لقد استلمنا دفعتك.</p><p><strong>المبلغ:</strong> {{amount}} ريال</p><p><strong>رقم التذكرة:</strong> {{ticket_number}}</p><p><strong>الرصيد المتبقي:</strong> {{remaining_balance}} ريال</p>',
                'text_content': 'We have received your payment. Amount: {{amount}} SAR, Ticket Number: {{ticket_number}}, Remaining Balance: {{remaining_balance}} SAR',
                'text_content_ar': 'لقد استلمنا دفعتك. المبلغ: {{amount}} ريال، رقم التذكرة: {{ticket_number}}، الرصيد المتبقي: {{remaining_balance}} ريال'
            },
            {
                'template_type': 'payment_due',
                'subject': 'Payment Due Reminder',
                'subject_ar': 'تذكير بالدفع المستحق',
                'html_content': '<h1>Payment Due</h1><p>You have a payment due.</p><p><strong>Amount:</strong> {{amount}} SAR</p><p><strong>Due Date:</strong> {{due_date}}</p><p><strong>Ticket Number:</strong> {{ticket_number}}</p>',
                'html_content_ar': '<h1>دفع مستحق</h1><p>لديك دفعة مستحقة.</p><p><strong>المبلغ:</strong> {{amount}} ريال</p><p><strong>تاريخ الاستحقاق:</strong> {{due_date}}</p><p><strong>رقم التذكرة:</strong> {{ticket_number}}</p>',
                'text_content': 'You have a payment due. Amount: {{amount}} SAR, Due Date: {{due_date}}, Ticket Number: {{ticket_number}}',
                'text_content_ar': 'لديك دفعة مستحقة. المبلغ: {{amount}} ريال، تاريخ الاستحقاق: {{due_date}}، رقم التذكرة: {{ticket_number}}'
            }
        ]
        
        created_count = 0
        for template_data in templates_data:
            template, created = NotificationTemplate.objects.get_or_create(
                template_type=template_data['template_type'],
                defaults=template_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'  Created notification template: {template.template_type}')
        
        self.stdout.write(f'  Notification templates created: {created_count}')
    
    def create_admin_user(self):
        """Create default admin user for finance app"""
        FinanceUser = get_user_model()
        
        email = 'finance.admin@mushqila.com'
        password = 'FinanceAdmin123!'
        
        if not FinanceUser.objects.filter(email=email).exists():
            admin_user = FinanceUser.objects.create_user(
                email=email,
                password=password,
                first_name='Finance',
                last_name='Administrator',
                user_type=FinanceUser.UserType.ADMIN,
                status=FinanceUser.Status.ACTIVE,
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            
            # Create user profile
            from finance.models import FinanceUserProfile
            FinanceUserProfile.objects.create(
                user=admin_user,
                company_name='Mushqila Finance',
                language='en',
                timezone='Asia/Riyadh'
            )
            
            self.stdout.write(f'  Created admin user: {email}')
            self.stdout.write(f'  Password: {password}')
        else:
            self.stdout.write(f'  Admin user already exists: {email}')
