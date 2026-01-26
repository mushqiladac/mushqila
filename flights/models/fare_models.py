# flights/models/fare_models.py
"""
Fare rules and pricing models for B2B Travel Platform
Production Ready - Final Version
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import uuid


class Fare(models.Model):
    """Base fare information with comprehensive pricing details"""
    
    class FareType(models.TextChoices):
        PUBLISHED = 'published', _('Published Fare')
        PRIVATE = 'private', _('Private Fare')
        NET = 'net', _('Net Fare')
        NEGOTIATED = 'negotiated', _('Negotiated Fare')
        CORPORATE = 'corporate', _('Corporate Fare')
        CONSOLIDATOR = 'consolidator', _('Consolidator Fare')
        GROUP = 'group', _('Group Fare')
        PROMOTIONAL = 'promotional', _('Promotional Fare')
        MILITARY = 'military', _('Military Fare')
        STUDENT = 'student', _('Student Fare')
        SENIOR = 'senior', _('Senior Citizen Fare')
    
    class FareStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        EXPIRED = 'expired', _('Expired')
        SUSPENDED = 'suspended', _('Suspended')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Fare Identification
    fare_basis = models.CharField(_('Fare Basis Code'), max_length=20, db_index=True)
    airline = models.ForeignKey('Airline', on_delete=models.CASCADE, 
                               verbose_name=_('Airline'))
    
    # Route Information
    origin = models.ForeignKey('Airport', on_delete=models.CASCADE, 
                              related_name='fare_origins', verbose_name=_('Origin'))
    destination = models.ForeignKey('Airport', on_delete=models.CASCADE, 
                                   related_name='fare_destinations', verbose_name=_('Destination'))
    
    # Fare Details
    fare_type = models.CharField(_('Fare Type'), max_length=20, 
                                choices=FareType.choices, default=FareType.PUBLISHED)
    status = models.CharField(_('Status'), max_length=20, 
                             choices=FareStatus.choices, default=FareStatus.ACTIVE)
    cabin_class = models.CharField(_('Cabin Class'), max_length=20)
    booking_class = models.CharField(_('Booking Class'), max_length=1)
    
    # Pricing Information
    base_fare = models.DecimalField(_('Base Fare'), max_digits=12, decimal_places=2)
    currency = models.CharField(_('Currency'), max_length=3, default='SAR')
    
    # Validity Period
    effective_date = models.DateField(_('Effective Date'))
    expiry_date = models.DateField(_('Expiry Date'))
    last_ticketing_date = models.DateField(_('Last Ticketing Date'), null=True, blank=True)
    
    # Travel Restrictions
    minimum_stay = models.PositiveIntegerField(_('Minimum Stay (days)'), default=0)
    maximum_stay = models.PositiveIntegerField(_('Maximum Stay (days)'), default=365)
    advance_purchase = models.PositiveIntegerField(_('Advance Purchase (days)'), default=0)
    
    # Seasonality
    season_start = models.DateField(_('Season Start'), null=True, blank=True)
    season_end = models.DateField(_('Season End'), null=True, blank=True)
    blackout_dates = models.JSONField(_('Blackout Dates'), default=list, blank=True)
    
    # Day/Time Restrictions
    day_restrictions = models.JSONField(_('Day Restrictions'), default=dict, blank=True)
    time_restrictions = models.JSONField(_('Time Restrictions'), default=dict, blank=True)
    
    # Fare Rules
    is_refundable = models.BooleanField(_('Is Refundable'), default=False)
    is_changeable = models.BooleanField(_('Is Changeable'), default=False)
    is_routable = models.BooleanField(_('Is Routable'), default=True)
    is_combinable = models.BooleanField(_('Is Combinable'), default=True)
    
    # Penalties
    cancellation_penalty = models.DecimalField(_('Cancellation Penalty'), max_digits=10, 
                                              decimal_places=2, default=0)
    change_penalty = models.DecimalField(_('Change Penalty'), max_digits=10, 
                                        decimal_places=2, default=0)
    no_show_penalty = models.DecimalField(_('No Show Penalty'), max_digits=10, 
                                         decimal_places=2, default=0)
    
    # Passenger Restrictions
    adult_applicable = models.BooleanField(_('Adult Applicable'), default=True)
    child_applicable = models.BooleanField(_('Child Applicable'), default=True)
    infant_applicable = models.BooleanField(_('Infant Applicable'), default=True)
    child_discount_rate = models.DecimalField(_('Child Discount Rate'), max_digits=5, 
                                             decimal_places=2, default=0)
    infant_discount_rate = models.DecimalField(_('Infant Discount Rate'), max_digits=5, 
                                              decimal_places=2, default=0)
    
    # GDS Information
    gds_fare_id = models.CharField(_('GDS Fare ID'), max_length=100, blank=True)
    gds_provider = models.CharField(_('GDS Provider'), max_length=20, default='travelport')
    gds_fare_basis_key = models.CharField(_('GDS Fare Basis Key'), max_length=50, blank=True)
    
    # Corporate Information
    corporate_client = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                        null=True, blank=True, 
                                        related_name='corporate_fares',
                                        verbose_name=_('Corporate Client'))
    contract_number = models.CharField(_('Contract Number'), max_length=50, blank=True)
    
    # Metadata
    fare_notes = models.TextField(_('Fare Notes'), blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                  null=True, blank=True, 
                                  related_name='created_fares',
                                  verbose_name=_('Created By'))
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('fare')
        verbose_name_plural = _('fares')
        ordering = ['airline', 'fare_basis']
        indexes = [
            models.Index(fields=['fare_basis', 'airline']),
            models.Index(fields=['origin', 'destination', 'effective_date']),
            models.Index(fields=['status', 'expiry_date']),
            models.Index(fields=['corporate_client', 'status']),
        ]
        unique_together = ['fare_basis', 'airline', 'origin', 'destination', 'cabin_class']
    
    def __str__(self):
        return f"{self.airline.code} {self.fare_basis}: {self.origin} → {self.destination}"
    
    def is_valid(self):
        """Check if fare is currently valid"""
        today = timezone.now().date()
        return (self.status == self.FareStatus.ACTIVE and
                self.effective_date <= today <= self.expiry_date)
    
    def calculate_fare_for_passenger(self, passenger_type='ADT'):
        """Calculate fare for specific passenger type"""
        base_fare = self.base_fare
        
        if passenger_type == 'CHD' and self.child_applicable:
            discount = (base_fare * self.child_discount_rate) / Decimal('100')
            return base_fare - discount
        elif passenger_type == 'INF' and self.infant_applicable:
            discount = (base_fare * self.infant_discount_rate) / Decimal('100')
            return base_fare - discount
        
        return base_fare if passenger_type == 'ADT' else Decimal('0.00')


class FareComponent(models.Model):
    """Detailed fare components (taxes, fees, surcharges)"""
    
    class ComponentType(models.TextChoices):
        BASE_FARE = 'base_fare', _('Base Fare')
        TAX = 'tax', _('Tax')
        FEE = 'fee', _('Fee')
        SURCHARGE = 'surcharge', _('Surcharge')
        COMMISSION = 'commission', _('Commission')
        MARKUP = 'markup', _('Markup')
        DISCOUNT = 'discount', _('Discount')
        INSURANCE = 'insurance', _('Insurance')
        SERVICE_FEE = 'service_fee', _('Service Fee')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fare = models.ForeignKey(Fare, on_delete=models.CASCADE, 
                            related_name='components', verbose_name=_('Fare'))
    
    # Component Information
    component_type = models.CharField(_('Component Type'), max_length=20, 
                                     choices=ComponentType.choices)
    code = models.CharField(_('Component Code'), max_length=10)
    description = models.CharField(_('Description'), max_length=200)
    description_ar = models.CharField(_('Description (Arabic)'), max_length=200, blank=True)
    
    # Pricing
    amount = models.DecimalField(_('Amount'), max_digits=12, decimal_places=2)
    currency = models.CharField(_('Currency'), max_length=3, default='SAR')
    is_percentage = models.BooleanField(_('Is Percentage'), default=False)
    percentage_of = models.CharField(_('Percentage Of'), max_length=20, blank=True)
    
    # Applicability
    passenger_type = models.CharField(_('Passenger Type'), max_length=3, 
                                     choices=[('ADT', 'Adult'), ('CHD', 'Child'), ('INF', 'Infant')],
                                     default='ADT')
    mandatory = models.BooleanField(_('Mandatory'), default=True)
    refundable = models.BooleanField(_('Refundable'), default=False)
    
    # Tax Specific Information
    tax_type = models.CharField(_('Tax Type'), max_length=50, blank=True)
    tax_country = models.CharField(_('Tax Country'), max_length=2, blank=True)
    tax_authority = models.CharField(_('Tax Authority'), max_length=100, blank=True)
    
    # GDS Information
    gds_component_code = models.CharField(_('GDS Component Code'), max_length=10, blank=True)
    
    class Meta:
        verbose_name = _('fare component')
        verbose_name_plural = _('fare components')
        ordering = ['component_type', 'code']
        indexes = [
            models.Index(fields=['fare', 'component_type']),
            models.Index(fields=['code', 'passenger_type']),
        ]
    
    def __str__(self):
        return f"{self.get_component_type_display()}: {self.code} - {self.amount} {self.currency}"
    
    def calculate_amount(self, base_amount=Decimal('0.00')):
        """Calculate component amount"""
        if self.is_percentage and base_amount:
            return (base_amount * self.amount) / Decimal('100.00')
        return self.amount


class Tax(models.Model):
    """Tax information for flights"""
    
    class TaxType(models.TextChoices):
        AIRPORT_TAX = 'airport_tax', _('Airport Tax')
        SECURITY_TAX = 'security_tax', _('Security Tax')
        FUEL_SURCHARGE = 'fuel_surcharge', _('Fuel Surcharge')
        GOVERNMENT_TAX = 'government_tax', _('Government Tax')
        VALUE_ADDED_TAX = 'vat', _('Value Added Tax (VAT)')
        TOURISM_TAX = 'tourism_tax', _('Tourism Tax')
        ENVIRONMENTAL_TAX = 'environmental_tax', _('Environmental Tax')
        PASSENGER_SERVICE = 'passenger_service', _('Passenger Service Charge')
        NAVIGATION_FEE = 'navigation_fee', _('Navigation Fee')
    
    code = models.CharField(_('Tax Code'), max_length=10, primary_key=True)
    tax_type = models.CharField(_('Tax Type'), max_length=30, choices=TaxType.choices)
    description = models.CharField(_('Description'), max_length=200)
    description_ar = models.CharField(_('Description (Arabic)'), max_length=200, blank=True)
    
    # Tax Information
    country = models.CharField(_('Country'), max_length=2)
    authority = models.CharField(_('Tax Authority'), max_length=100, blank=True)
    website = models.URLField(_('Website'), blank=True)
    
    # Rate Information
    is_percentage = models.BooleanField(_('Is Percentage'), default=False)
    fixed_amount = models.DecimalField(_('Fixed Amount'), max_digits=10, 
                                      decimal_places=2, null=True, blank=True)
    percentage_rate = models.DecimalField(_('Percentage Rate'), max_digits=5, 
                                         decimal_places=2, null=True, blank=True)
    minimum_amount = models.DecimalField(_('Minimum Amount'), max_digits=10, 
                                        decimal_places=2, null=True, blank=True)
    maximum_amount = models.DecimalField(_('Maximum Amount'), max_digits=10, 
                                        decimal_places=2, null=True, blank=True)
    
    # Applicability
    applicable_classes = models.JSONField(_('Applicable Classes'), default=list, blank=True)
    exempt_passenger_types = models.JSONField(_('Exempt Passenger Types'), 
                                             default=list, blank=True)
    exempt_countries = models.JSONField(_('Exempt Countries'), default=list, blank=True)
    
    # Saudi Arabia Specific
    saudi_vat_applicable = models.BooleanField(_('Saudi VAT Applicable'), default=False)
    vat_rate = models.DecimalField(_('VAT Rate'), max_digits=5, 
                                  decimal_places=2, null=True, blank=True)
    
    # Validity
    effective_date = models.DateField(_('Effective Date'))
    expiry_date = models.DateField(_('Expiry Date'), null=True, blank=True)
    is_active = models.BooleanField(_('Is Active'), default=True)
    
    # GDS Information
    gds_tax_codes = models.JSONField(_('GDS Tax Codes'), default=dict, blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('tax')
        verbose_name_plural = _('taxes')
        ordering = ['country', 'code']
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['country', 'tax_type']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.description}"
    
    def calculate_tax(self, base_amount=Decimal('0.00'), passenger_type='ADT'):
        """Calculate tax amount"""
        if passenger_type in self.exempt_passenger_types:
            return Decimal('0.00')
        
        if self.is_percentage and self.percentage_rate:
            tax_amount = (base_amount * self.percentage_rate) / Decimal('100.00')
        else:
            tax_amount = self.fixed_amount or Decimal('0.00')
        
        # Apply minimum/maximum limits
        if self.minimum_amount and tax_amount < self.minimum_amount:
            tax_amount = self.minimum_amount
        if self.maximum_amount and tax_amount > self.maximum_amount:
            tax_amount = self.maximum_amount
        
        return tax_amount
    
    def is_applicable(self, passenger_type='ADT', cabin_class='economy'):
        """Check if tax is applicable"""
        if passenger_type in self.exempt_passenger_types:
            return False
        
        if self.applicable_classes and cabin_class not in self.applicable_classes:
            return False
        
        return self.is_active


class CommissionRule(models.Model):
    """Commission rules for agents and airlines"""
    
    class CommissionType(models.TextChoices):
        PERCENTAGE = 'percentage', _('Percentage')
        FIXED = 'fixed', _('Fixed Amount')
        TIERED = 'tiered', _('Tiered')
        SLAB = 'slab', _('Slab Based')
    
    class CommissionBasis(models.TextChoices):
        BASE_FARE = 'base_fare', _('Base Fare')
        TOTAL_FARE = 'total_fare', _('Total Fare')
        NET_FARE = 'net_fare', _('Net Fare')
        TICKET_VALUE = 'ticket_value', _('Ticket Value')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Rule Information
    rule_name = models.CharField(_('Rule Name'), max_length=200)
    commission_type = models.CharField(_('Commission Type'), max_length=20, 
                                      choices=CommissionType.choices, 
                                      default=CommissionType.PERCENTAGE)
    commission_basis = models.CharField(_('Commission Basis'), max_length=20, 
                                       choices=CommissionBasis.choices, 
                                       default=CommissionBasis.BASE_FARE)
    
    # Applicability
    airline = models.ForeignKey('Airline', on_delete=models.CASCADE, 
                               null=True, blank=True, verbose_name=_('Airline'))
    agent = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                            null=True, blank=True, 
                            related_name='commission_rules',
                            verbose_name=_('Agent'))
    agent_type = models.CharField(_('Agent Type'), max_length=20, 
                                 choices=[('all', 'All Agents'), 
                                         ('super_agent', 'Super Agent'),
                                         ('agent', 'Agent'), 
                                         ('sub_agent', 'Sub Agent'),
                                         ('corporate', 'Corporate')],
                                 default='all')
    
    # Route Specific
    origin = models.ForeignKey('Airport', on_delete=models.CASCADE, 
                              related_name='commission_origins', 
                              null=True, blank=True, verbose_name=_('Origin'))
    destination = models.ForeignKey('Airport', on_delete=models.CASCADE, 
                                   related_name='commission_destinations', 
                                   null=True, blank=True, verbose_name=_('Destination'))
    cabin_class = models.CharField(_('Cabin Class'), max_length=20, blank=True)
    
    # Commission Rates
    commission_rate = models.DecimalField(_('Commission Rate'), max_digits=5, 
                                         decimal_places=2, default=Decimal('0.00'))
    fixed_amount = models.DecimalField(_('Fixed Amount'), max_digits=10, 
                                      decimal_places=2, null=True, blank=True)
    
    # Tiered Commission (for slab-based)
    tier_rules = models.JSONField(_('Tier Rules'), default=list, blank=True)
    
    # Validity
    effective_date = models.DateField(_('Effective Date'))
    expiry_date = models.DateField(_('Expiry Date'), null=True, blank=True)
    is_active = models.BooleanField(_('Is Active'), default=True)
    
    # Minimum/Maximum
    minimum_booking_value = models.DecimalField(_('Minimum Booking Value'), 
                                               max_digits=12, decimal_places=2, 
                                               null=True, blank=True)
    maximum_commission = models.DecimalField(_('Maximum Commission'), 
                                            max_digits=12, decimal_places=2, 
                                            null=True, blank=True)
    
    # Conditions
    domestic_only = models.BooleanField(_('Domestic Only'), default=False)
    international_only = models.BooleanField(_('International Only'), default=False)
    round_trip_only = models.BooleanField(_('Round Trip Only'), default=False)
    group_booking_only = models.BooleanField(_('Group Booking Only'), default=False)
    
    # Additional Incentives
    override_commission = models.DecimalField(_('Override Commission'), 
                                            max_digits=5, decimal_places=2, 
                                            null=True, blank=True)
    bonus_commission = models.DecimalField(_('Bonus Commission'), max_digits=5, 
                                          decimal_places=2, null=True, blank=True)
    
    # Metadata
    description = models.TextField(_('Description'), blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                  null=True, blank=True, 
                                  related_name='created_commission_rules',
                                  verbose_name=_('Created By'))
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('commission rule')
        verbose_name_plural = _('commission rules')
        ordering = ['-effective_date']
        indexes = [
            models.Index(fields=['airline', 'is_active']),
            models.Index(fields=['agent_type', 'effective_date']),
            models.Index(fields=['is_active', 'expiry_date']),
        ]
    
    def __str__(self):
        return f"Commission Rule: {self.rule_name}"
    
    def calculate_commission(self, booking_value, passenger_count=1):
        """Calculate commission based on rule"""
        if self.commission_type == self.CommissionType.FIXED:
            commission = self.fixed_amount or Decimal('0.00')
        elif self.commission_type == self.CommissionType.TIERED:
            commission = self._calculate_tiered_commission(booking_value)
        else:  # Percentage
            commission = (booking_value * self.commission_rate) / Decimal('100.00')
        
        # Apply maximum commission limit
        if self.maximum_commission and commission > self.maximum_commission:
            commission = self.maximum_commission
        
        # Apply per passenger if needed
        return commission * passenger_count
    
    def _calculate_tiered_commission(self, booking_value):
        """Calculate tiered commission"""
        for tier in self.tier_rules:
            min_val = Decimal(str(tier.get('min', 0)))
            max_val = Decimal(str(tier.get('max', float('inf'))))
            
            if min_val <= booking_value <= max_val:
                if tier.get('type') == 'percentage':
                    return (booking_value * Decimal(str(tier.get('rate', 0)))) / Decimal('100.00')
                else:
                    return Decimal(str(tier.get('amount', 0)))
        
        return Decimal('0.00')


class MarkupRule(models.Model):
    """Markup rules for pricing"""
    
    class MarkupType(models.TextChoices):
        PERCENTAGE = 'percentage', _('Percentage')
        FIXED = 'fixed', _('Fixed Amount')
        DYNAMIC = 'dynamic', _('Dynamic')
    
    class MarkupBasis(models.TextChoices):
        BASE_FARE = 'base_fare', _('Base Fare')
        TOTAL_FARE = 'total_fare', _('Total Fare')
        NET_FARE = 'net_fare', _('Net Fare')
        COMPETITOR_PRICE = 'competitor_price', _('Competitor Price')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Rule Information
    rule_name = models.CharField(_('Rule Name'), max_length=200)
    markup_type = models.CharField(_('Markup Type'), max_length=20, 
                                  choices=MarkupType.choices, default=MarkupType.PERCENTAGE)
    markup_basis = models.CharField(_('Markup Basis'), max_length=20, 
                                   choices=MarkupBasis.choices, default=MarkupBasis.BASE_FARE)
    
    # Applicability
    airline = models.ForeignKey('Airline', on_delete=models.CASCADE, 
                               null=True, blank=True, verbose_name=_('Airline'))
    agent = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                            null=True, blank=True, 
                            related_name='markup_rules',
                            verbose_name=_('Agent'))
    agent_type = models.CharField(_('Agent Type'), max_length=20, 
                                 choices=[('all', 'All Agents'), 
                                         ('super_agent', 'Super Agent'),
                                         ('agent', 'Agent'), 
                                         ('sub_agent', 'Sub Agent'),
                                         ('corporate', 'Corporate')],
                                 default='all')
    
    # Route Specific
    origin = models.ForeignKey('Airport', on_delete=models.CASCADE, 
                              related_name='markup_origins', 
                              null=True, blank=True, verbose_name=_('Origin'))
    destination = models.ForeignKey('Airport', on_delete=models.CASCADE, 
                                   related_name='markup_destinations', 
                                   null=True, blank=True, verbose_name=_('Destination'))
    cabin_class = models.CharField(_('Cabin Class'), max_length=20, blank=True)
    
    # Markup Rates
    markup_rate = models.DecimalField(_('Markup Rate'), max_digits=5, 
                                     decimal_places=2, default=Decimal('0.00'))
    fixed_amount = models.DecimalField(_('Fixed Amount'), max_digits=10, 
                                      decimal_places=2, null=True, blank=True)
    
    # Dynamic Markup Rules
    dynamic_rules = models.JSONField(_('Dynamic Rules'), default=dict, blank=True)
    
    # Validity
    effective_date = models.DateField(_('Effective Date'))
    expiry_date = models.DateField(_('Expiry Date'), null=True, blank=True)
    is_active = models.BooleanField(_('Is Active'), default=True)
    
    # Minimum/Maximum
    minimum_markup = models.DecimalField(_('Minimum Markup'), max_digits=10, 
                                        decimal_places=2, null=True, blank=True)
    maximum_markup = models.DecimalField(_('Maximum Markup'), max_digits=10, 
                                        decimal_places=2, null=True, blank=True)
    
    # Conditions
    domestic_only = models.BooleanField(_('Domestic Only'), default=False)
    international_only = models.BooleanField(_('International Only'), default=False)
    peak_season_only = models.BooleanField(_('Peak Season Only'), default=False)
    last_minute_only = models.BooleanField(_('Last Minute Only'), default=False)
    
    # Competitor Based
    competitor_markup_rules = models.JSONField(_('Competitor Markup Rules'), 
                                              default=dict, blank=True)
    
    # Metadata
    description = models.TextField(_('Description'), blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                  null=True, blank=True, 
                                  related_name='created_markup_rules',
                                  verbose_name=_('Created By'))
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('markup rule')
        verbose_name_plural = _('markup rules')
        ordering = ['-effective_date']
        indexes = [
            models.Index(fields=['airline', 'is_active']),
            models.Index(fields=['agent_type', 'effective_date']),
        ]
    
    def __str__(self):
        return f"Markup Rule: {self.rule_name}"
    
    def calculate_markup(self, base_amount, competitor_price=None):
        """Calculate markup based on rule"""
        if self.markup_type == self.MarkupType.FIXED:
            markup = self.fixed_amount or Decimal('0.00')
        elif self.markup_type == self.MarkupType.DYNAMIC:
            markup = self._calculate_dynamic_markup(base_amount, competitor_price)
        else:  # Percentage
            markup = (base_amount * self.markup_rate) / Decimal('100.00')
        
        # Apply minimum/maximum limits
        if self.minimum_markup and markup < self.minimum_markup:
            markup = self.minimum_markup
        if self.maximum_markup and markup > self.maximum_markup:
            markup = self.maximum_markup
        
        return markup
    
    def _calculate_dynamic_markup(self, base_amount, competitor_price):
        """Calculate dynamic markup"""
        # Implement dynamic pricing logic based on rules
        return Decimal('0.00')


class CorporateFare(models.Model):
    """Corporate/negotiated fares for specific clients"""
    
    class FareStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        PENDING = 'pending', _('Pending Approval')
        EXPIRED = 'expired', _('Expired')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Corporate Information
    corporate_client = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                                        related_name='corporate_fares_list',
                                        verbose_name=_('Corporate Client'))
    contract_number = models.CharField(_('Contract Number'), max_length=50)
    contract_name = models.CharField(_('Contract Name'), max_length=200)
    
    # Airline Information
    airline = models.ForeignKey('Airline', on_delete=models.CASCADE, 
                               verbose_name=_('Airline'))
    
    # Route Information
    origin = models.ForeignKey('Airport', on_delete=models.CASCADE, 
                              related_name='corporate_fare_origins', 
                              verbose_name=_('Origin'))
    destination = models.ForeignKey('Airport', on_delete=models.CASCADE, 
                                   related_name='corporate_fare_destinations', 
                                   verbose_name=_('Destination'))
    
    # Fare Details
    fare_basis = models.CharField(_('Fare Basis'), max_length=20)
    cabin_class = models.CharField(_('Cabin Class'), max_length=20)
    corporate_fare_amount = models.DecimalField(_('Corporate Fare Amount'), 
                                               max_digits=12, decimal_places=2)
    published_fare_amount = models.DecimalField(_('Published Fare Amount'), 
                                               max_digits=12, decimal_places=2)
    currency = models.CharField(_('Currency'), max_length=3, default='SAR')
    
    # Discount Information
    discount_percentage = models.DecimalField(_('Discount Percentage'), max_digits=5, 
                                             decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(_('Discount Amount'), max_digits=10, 
                                         decimal_places=2, default=Decimal('0.00'))
    
    # Validity
    effective_date = models.DateField(_('Effective Date'))
    expiry_date = models.DateField(_('Expiry Date'))
    status = models.CharField(_('Status'), max_length=20, 
                             choices=FareStatus.choices, default=FareStatus.ACTIVE)
    
    # Travel Restrictions
    advance_purchase_days = models.PositiveIntegerField(_('Advance Purchase Days'), default=0)
    minimum_stay_days = models.PositiveIntegerField(_('Minimum Stay Days'), default=0)
    maximum_stay_days = models.PositiveIntegerField(_('Maximum Stay Days'), default=365)
    
    # Passenger Restrictions
    allowed_passenger_types = models.JSONField(_('Allowed Passenger Types'), 
                                              default=list, blank=True)
    maximum_passengers = models.PositiveIntegerField(_('Maximum Passengers'), 
                                                    null=True, blank=True)
    
    # Booking Rules
    booking_channel = models.CharField(_('Booking Channel'), max_length=50, 
                                      choices=[('all', 'All Channels'), 
                                              ('web', 'Web Only'),
                                              ('mobile', 'Mobile Only'),
                                              ('api', 'API Only')],
                                      default='all')
    require_approval = models.BooleanField(_('Require Approval'), default=False)
    approval_workflow = models.JSONField(_('Approval Workflow'), default=dict, blank=True)
    
    # Usage Limits
    monthly_quota = models.PositiveIntegerField(_('Monthly Quota'), null=True, blank=True)
    quarterly_quota = models.PositiveIntegerField(_('Quarterly Quota'), null=True, blank=True)
    yearly_quota = models.PositiveIntegerField(_('Yearly Quota'), null=True, blank=True)
    used_quota = models.PositiveIntegerField(_('Used Quota'), default=0)
    
    # Cost Center Allocation
    cost_centers = models.JSONField(_('Cost Centers'), default=list, blank=True)
    project_codes = models.JSONField(_('Project Codes'), default=list, blank=True)
    
    # GDS Information
    gds_corporate_id = models.CharField(_('GDS Corporate ID'), max_length=100, blank=True)
    gds_pseudo_city_code = models.CharField(_('GDS Pseudo City Code'), max_length=10, blank=True)
    
    # Metadata
    terms_and_conditions = models.TextField(_('Terms and Conditions'), blank=True)
    notes = models.TextField(_('Notes'), blank=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('corporate fare')
        verbose_name_plural = _('corporate fares')
        ordering = ['corporate_client', 'airline', 'origin']
        indexes = [
            models.Index(fields=['corporate_client', 'status']),
            models.Index(fields=['airline', 'origin', 'destination']),
            models.Index(fields=['status', 'expiry_date']),
            models.Index(fields=['contract_number']),
        ]
        unique_together = ['corporate_client', 'airline', 'origin', 'destination', 'cabin_class']
    
    def __str__(self):
        return f"{self.corporate_client} - {self.airline.code}: {self.origin} → {self.destination}"
    
    def is_valid(self):
        """Check if corporate fare is valid"""
        today = timezone.now().date()
        return (self.status == self.FareStatus.ACTIVE and
                self.effective_date <= today <= self.expiry_date and
                (not self.monthly_quota or self.used_quota < self.monthly_quota))
    
    def calculate_savings(self):
        """Calculate savings compared to published fare"""
        return self.published_fare_amount - self.corporate_fare_amount
    
    def get_savings_percentage(self):
        """Calculate savings percentage"""
        if self.published_fare_amount > 0:
            return ((self.published_fare_amount - self.corporate_fare_amount) / 
                    self.published_fare_amount * 100)
        return Decimal('0.00')


class PromoCode(models.Model):
    """Promotional codes for discounts"""
    
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', _('Percentage')
        FIXED_AMOUNT = 'fixed_amount', _('Fixed Amount')
        FREE_SERVICE = 'free_service', _('Free Service')
    
    class ApplicableTo(models.TextChoices):
        ALL = 'all', _('All Bookings')
        SPECIFIC_AIRLINE = 'specific_airline', _('Specific Airline')
        SPECIFIC_ROUTE = 'specific_route', _('Specific Route')
        CORPORATE_CLIENT = 'corporate_client', _('Corporate Client')
        AGENT_TYPE = 'agent_type', _('Agent Type')
    
    class PromoStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        EXPIRED = 'expired', _('Expired')
        USED_UP = 'used_up', _('Used Up')
    
    code = models.CharField(_('Promo Code'), max_length=50, primary_key=True)
    name = models.CharField(_('Promo Name'), max_length=200)
    
    # Discount Information
    discount_type = models.CharField(_('Discount Type'), max_length=20, 
                                    choices=DiscountType.choices, 
                                    default=DiscountType.PERCENTAGE)
    discount_value = models.DecimalField(_('Discount Value'), max_digits=10, 
                                        decimal_places=2)
    currency = models.CharField(_('Currency'), max_length=3, default='SAR')
    
    # Applicability
    applicable_to = models.CharField(_('Applicable To'), max_length=20, 
                                    choices=ApplicableTo.choices, default=ApplicableTo.ALL)
    airline = models.ForeignKey('Airline', on_delete=models.CASCADE, 
                               null=True, blank=True, verbose_name=_('Airline'))
    origin = models.ForeignKey('Airport', on_delete=models.CASCADE, 
                              related_name='promo_origins', 
                              null=True, blank=True, verbose_name=_('Origin'))
    destination = models.ForeignKey('Airport', on_delete=models.CASCADE, 
                                   related_name='promo_destinations', 
                                   null=True, blank=True, verbose_name=_('Destination'))
    corporate_client = models.ForeignKey('accounts.User', on_delete=models.CASCADE, 
                                        null=True, blank=True, 
                                        related_name='promo_codes',
                                        verbose_name=_('Corporate Client'))
    agent_type = models.CharField(_('Agent Type'), max_length=20, blank=True)
    
    # Usage Limits
    max_usage = models.PositiveIntegerField(_('Maximum Usage'), null=True, blank=True)
    usage_count = models.PositiveIntegerField(_('Usage Count'), default=0)
    max_usage_per_user = models.PositiveIntegerField(_('Max Usage Per User'), default=1)
    user_usage_tracking = models.JSONField(_('User Usage Tracking'), default=dict, blank=True)
    
    # Minimum Requirements
    minimum_booking_value = models.DecimalField(_('Minimum Booking Value'), 
                                               max_digits=12, decimal_places=2, 
                                               null=True, blank=True)
    minimum_passengers = models.PositiveIntegerField(_('Minimum Passengers'), default=1)
    
    # Validity
    valid_from = models.DateTimeField(_('Valid From'))
    valid_until = models.DateTimeField(_('Valid Until'))
    status = models.CharField(_('Status'), max_length=20, 
                             choices=PromoStatus.choices, default=PromoStatus.ACTIVE)
    
    # Additional Conditions
    cabin_class_restrictions = models.JSONField(_('Cabin Class Restrictions'), 
                                               default=list, blank=True)
    travel_date_restrictions = models.JSONField(_('Travel Date Restrictions'), 
                                               default=dict, blank=True)
    booking_date_restrictions = models.JSONField(_('Booking Date Restrictions'), 
                                                default=dict, blank=True)
    
    # Promo Details
    description = models.TextField(_('Description'), blank=True)
    terms_and_conditions = models.TextField(_('Terms and Conditions'), blank=True)
    marketing_message = models.TextField(_('Marketing Message'), blank=True)
    marketing_message_ar = models.TextField(_('Marketing Message (Arabic)'), blank=True)
    
    # Metadata
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, 
                                  null=True, blank=True, 
                                  related_name='created_promo_codes',
                                  verbose_name=_('Created By'))
    is_public = models.BooleanField(_('Is Public'), default=False)
    is_redeemable = models.BooleanField(_('Is Redeemable'), default=True)
    
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    class Meta:
        verbose_name = _('promo code')
        verbose_name_plural = _('promo codes')
        ordering = ['-valid_from']
        indexes = [
            models.Index(fields=['code', 'status']),
            models.Index(fields=['applicable_to', 'valid_until']),
            models.Index(fields=['status', 'valid_until']),
        ]
    
    def __str__(self):
        return f"Promo: {self.code} - {self.name}"
    
    def is_valid(self, user=None, booking_value=Decimal('0.00')):
        """Check if promo code is valid for use"""
        now = timezone.now()
        
        # Basic validity checks
        if (self.status != self.PromoStatus.ACTIVE or
            now < self.valid_from or now > self.valid_until or
            (self.max_usage and self.usage_count >= self.max_usage)):
            return False
        
        # User specific checks
        if user and self.max_usage_per_user > 0:
            user_usage = self.user_usage_tracking.get(str(user.id), 0)
            if user_usage >= self.max_usage_per_user:
                return False
        
        # Minimum requirements
        if (self.minimum_booking_value and 
            booking_value < self.minimum_booking_value):
            return False
        
        return True
    
    def calculate_discount(self, booking_value):
        """Calculate discount amount"""
        if self.discount_type == self.DiscountType.PERCENTAGE:
            return (booking_value * self.discount_value) / Decimal('100.00')
        elif self.discount_type == self.DiscountType.FIXED_AMOUNT:
            return min(self.discount_value, booking_value)
        else:
            return Decimal('0.00')
    
    def apply_promo(self, user):
        """Apply promo code and update usage"""
        if not self.is_valid(user):
            return False
        
        self.usage_count += 1
        
        # Track user usage
        if user:
            user_id = str(user.id)
            current_usage = self.user_usage_tracking.get(user_id, 0)
            self.user_usage_tracking[user_id] = current_usage + 1
        
        # Update status if max usage reached
        if self.max_usage and self.usage_count >= self.max_usage:
            self.status = self.PromoStatus.USED_UP
        
        self.save()
        return True