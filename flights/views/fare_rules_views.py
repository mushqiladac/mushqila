"""
Fare Rules Views for B2B Travel Platform
Production Ready - Final Version
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count, Prefetch
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.db import transaction
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import re

# Optional imports for models
try:
    from flights.models import (
        Fare, FareRule, BaggageRule, FlightItinerary, Booking,
        Airline, Airport, FareComponent
    )
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False

# Optional imports for forms
try:
    from flights.forms import FareSearchForm, FareRuleFilterForm
    FORMS_AVAILABLE = True
except ImportError:
    FORMS_AVAILABLE = False

# Optional imports for services
try:
    from flights.services.fare_service import FareService
except ImportError:
    FareService = None

try:
    from flights.services.gds_service import GDSFareService
except ImportError:
    GDSFareService = None

try:
    from flights.services.parsing_service import FareRuleParser
except ImportError:
    FareRuleParser = None

try:
    from flights.utils.export import ExportUtils
except ImportError:
    ExportUtils = None

logger = logging.getLogger(__name__)


class FareRulesListView(LoginRequiredMixin, View):
    """List all fare rules with search and filters"""
    
    template_name = 'flights/fare_rules/fare_rules_list.html'
    items_per_page = 25
    
    def get(self, request):
        try:
            # Get filter parameters
            airline_filter = request.GET.get('airline', 'all')
            origin_filter = request.GET.get('origin', '')
            destination_filter = request.GET.get('destination', '')
            cabin_class_filter = request.GET.get('cabin_class', 'all')
            status_filter = request.GET.get('status', 'active')
            search_query = request.GET.get('q', '').strip()
            sort_by = request.GET.get('sort', '-effective_date')
            page_number = request.GET.get('page', 1)
            
            # Base queryset
            fare_rules = FareRule.objects.select_related(
                'airline',
                'origin',
                'destination'
            ).prefetch_related(
                'applicable_classes'
            )
            
            # Apply filters
            if airline_filter != 'all':
                fare_rules = fare_rules.filter(airline__code=airline_filter)
            
            if origin_filter:
                fare_rules = fare_rules.filter(origin__iata_code=origin_filter)
            
            if destination_filter:
                fare_rules = fare_rules.filter(destination__iata_code=destination_filter)
            
            if cabin_class_filter != 'all':
                fare_rules = fare_rules.filter(cabin_class=cabin_class_filter)
            
            if status_filter == 'active':
                today = timezone.now().date()
                fare_rules = fare_rules.filter(
                    travel_date_start__lte=today,
                    travel_date_end__gte=today,
                    is_active=True
                )
            elif status_filter == 'expired':
                today = timezone.now().date()
                fare_rules = fare_rules.filter(
                    travel_date_end__lt=today
                )
            elif status_filter == 'future':
                today = timezone.now().date()
                fare_rules = fare_rules.filter(
                    travel_date_start__gt=today
                )
            
            # Apply search
            if search_query:
                fare_rules = fare_rules.filter(
                    Q(fare_basis__icontains=search_query) |
                    Q(rule_text__icontains=search_query) |
                    Q(rule_text_ar__icontains=search_query) |
                    Q(rule_number__icontains=search_query) |
                    Q(airline__name__icontains=search_query)
                )
            
            # Apply sorting
            valid_sort_fields = [
                'fare_basis', '-fare_basis', 'airline__name', '-airline__name',
                'effective_date', '-effective_date', 'expiry_date', '-expiry_date',
                'category', '-category'
            ]
            if sort_by in valid_sort_fields:
                fare_rules = fare_rules.order_by(sort_by)
            else:
                fare_rules = fare_rules.order_by('-effective_date')
            
            # Get statistics
            stats = self.get_fare_rule_statistics(fare_rules)
            
            # Pagination
            paginator = Paginator(fare_rules, self.items_per_page)
            page_obj = paginator.get_page(page_number)
            
            # Get filter options
            airlines = Airline.objects.filter(is_active=True).order_by('name')
            
            context = {
                'page_obj': page_obj,
                'airlines': airlines,
                'airline_filter': airline_filter,
                'origin_filter': origin_filter,
                'destination_filter': destination_filter,
                'cabin_class_filter': cabin_class_filter,
                'status_filter': status_filter,
                'search_query': search_query,
                'sort_by': sort_by,
                'stats': stats,
                'cabin_classes': [
                    ('all', 'All Classes'),
                    ('economy', 'Economy'),
                    ('premium_economy', 'Premium Economy'),
                    ('business', 'Business'),
                    ('first', 'First Class'),
                ],
                'status_options': [
                    ('active', 'Active'),
                    ('expired', 'Expired'),
                    ('future', 'Future'),
                    ('all', 'All'),
                ],
                'sort_options': [
                    ('-effective_date', 'Effective Date (Newest)'),
                    ('effective_date', 'Effective Date (Oldest)'),
                    ('-expiry_date', 'Expiry Date (Newest)'),
                    ('expiry_date', 'Expiry Date (Oldest)'),
                    ('airline__name', 'Airline (A-Z)'),
                    ('-airline__name', 'Airline (Z-A)'),
                    ('fare_basis', 'Fare Basis (A-Z)'),
                    ('-fare_basis', 'Fare Basis (Z-A)'),
                ]
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading fare rules list: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading fare rules. Please try again.')
            return render(request, self.template_name, {'page_obj': []})
    
    def get_fare_rule_statistics(self, fare_rules):
        """Calculate fare rule statistics"""
        today = timezone.now().date()
        
        stats = {
            'total_rules': fare_rules.count(),
            'active_rules': fare_rules.filter(
                travel_date_start__lte=today,
                travel_date_end__gte=today,
                is_active=True
            ).count(),
            'expired_rules': fare_rules.filter(
                travel_date_end__lt=today
            ).count(),
            'future_rules': fare_rules.filter(
                travel_date_start__gt=today
            ).count(),
        }
        
        # Category breakdown
        category_counts = fare_rules.values('category').annotate(count=Count('id'))
        stats['category_breakdown'] = {item['category']: item['count'] for item in category_counts}
        
        # Airline breakdown
        airline_counts = fare_rules.values('airline__code', 'airline__name').annotate(count=Count('id'))
        stats['airline_breakdown'] = {
            f"{item['airline__code']}": {
                'name': item['airline__name'],
                'count': item['count']
            }
            for item in airline_counts
        }
        
        return stats


class FareRuleDetailView(LoginRequiredMixin, View):
    """View detailed fare rule information"""
    
    template_name = 'flights/fare_rules/fare_rule_detail.html'
    
    def get(self, request, rule_id):
        try:
            # Get fare rule with all related data
            fare_rule = get_object_or_404(
                FareRule.objects.select_related(
                    'airline',
                    'origin',
                    'destination'
                ).prefetch_related(
                    'applicable_classes',
                    'excluded_classes',
                    'related_rules'
                ),
                id=rule_id
            )
            
            # Get related baggage rules
            baggage_rules = BaggageRule.objects.filter(
                airline=fare_rule.airline,
                cabin_class=fare_rule.cabin_class
            ).first()
            
            # Get fare rule parser service
            fare_service = FareService()
            
            # Parse rule text into structured data
            parsed_rules = fare_service.parse_fare_rule_text(fare_rule.rule_text)
            
            # Get similar fare rules
            similar_rules = FareRule.objects.filter(
                airline=fare_rule.airline,
                fare_basis=fare_rule.fare_basis
            ).exclude(id=fare_rule.id)[:5]
            
            # Get recent bookings using this fare rule
            recent_bookings = Booking.objects.filter(
                itinerary__segments__fare_basis=fare_rule.fare_basis
            ).select_related('agent', 'itinerary')[:10]
            
            context = {
                'fare_rule': fare_rule,
                'baggage_rules': baggage_rules,
                'parsed_rules': parsed_rules,
                'similar_rules': similar_rules,
                'recent_bookings': recent_bookings,
                'can_edit': request.user.user_type in ['admin', 'super_agent'],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading fare rule detail {rule_id}: {str(e)}", exc_info=True)
            messages.error(request, f'Error loading fare rule details: {str(e)}')
            return redirect('flights:fare_rules_list')


class FareRuleSearchView(LoginRequiredMixin, View):
    """Advanced fare rule search"""
    
    template_name = 'flights/fare_rules/fare_rule_search.html'
    
    def get(self, request):
        try:
            # Initialize forms
            search_form = FareSearchForm(request.GET or None)
            filter_form = FareRuleFilterForm(request.GET or None)
            
            # Get search results if form is submitted
            fare_rules = None
            search_performed = False
            
            if 'search' in request.GET and search_form.is_valid():
                fare_rules = self.perform_search(search_form.cleaned_data)
                search_performed = True
            
            context = {
                'search_form': search_form,
                'filter_form': filter_form,
                'fare_rules': fare_rules,
                'search_performed': search_performed,
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error in fare rule search: {str(e)}", exc_info=True)
            messages.error(request, 'Error performing search. Please try again.')
            return render(request, self.template_name, {
                'search_form': FareSearchForm(),
                'filter_form': FareRuleFilterForm(),
            })
    
    def perform_search(self, search_data):
        """Perform advanced fare rule search"""
        fare_rules = FareRule.objects.select_related(
            'airline', 'origin', 'destination'
        )
        
        # Apply search criteria
        if search_data.get('origin'):
            fare_rules = fare_rules.filter(origin__iata_code=search_data['origin'])
        
        if search_data.get('destination'):
            fare_rules = fare_rules.filter(destination__iata_code=search_data['destination'])
        
        if search_data.get('airline'):
            fare_rules = fare_rules.filter(airline__code=search_data['airline'])
        
        if search_data.get('fare_basis'):
            fare_rules = fare_rules.filter(fare_basis__icontains=search_data['fare_basis'])
        
        if search_data.get('cabin_class'):
            fare_rules = fare_rules.filter(cabin_class=search_data['cabin_class'])
        
        if search_data.get('travel_date'):
            travel_date = search_data['travel_date']
            fare_rules = fare_rules.filter(
                travel_date_start__lte=travel_date,
                travel_date_end__gte=travel_date
            )
        
        if search_data.get('rule_category'):
            fare_rules = fare_rules.filter(category=search_data['rule_category'])
        
        if search_data.get('rule_text'):
            rule_text = search_data['rule_text']
            fare_rules = fare_rules.filter(
                Q(rule_text__icontains=rule_text) |
                Q(rule_text_ar__icontains=rule_text)
            )
        
        # Filter by active rules only
        if search_data.get('active_only'):
            today = timezone.now().date()
            fare_rules = fare_rules.filter(
                travel_date_start__lte=today,
                travel_date_end__gte=today,
                is_active=True
            )
        
        return fare_rules.order_by('airline__code', 'fare_basis')


class FareRuleComparisonView(LoginRequiredMixin, View):
    """Compare multiple fare rules"""
    
    template_name = 'flights/fare_rules/fare_rule_comparison.html'
    
    def get(self, request):
        try:
            # Get rule IDs from query parameters
            rule_ids = request.GET.getlist('rules')
            
            if not rule_ids:
                messages.info(request, 'Please select fare rules to compare.')
                return redirect('flights:fare_rules_list')
            
            # Get fare rules
            fare_rules = FareRule.objects.filter(id__in=rule_ids).select_related(
                'airline', 'origin', 'destination'
            )
            
            if not fare_rules.exists():
                messages.error(request, 'No valid fare rules selected.')
                return redirect('flights:fare_rules_list')
            
            # Get fare service
            fare_service = FareService()
            
            # Parse and structure fare rules for comparison
            comparison_data = []
            for fare_rule in fare_rules:
                parsed_rules = fare_service.parse_fare_rule_text(fare_rule.rule_text)
                
                comparison_data.append({
                    'rule': fare_rule,
                    'parsed_rules': parsed_rules,
                    'baggage_rules': BaggageRule.objects.filter(
                        airline=fare_rule.airline,
                        cabin_class=fare_rule.cabin_class
                    ).first(),
                    'applicability': self.get_rule_applicability(fare_rule),
                })
            
            # Get comparison matrix
            comparison_matrix = self.create_comparison_matrix(comparison_data)
            
            context = {
                'comparison_data': comparison_data,
                'comparison_matrix': comparison_matrix,
                'selected_rules': [str(rule.id) for rule in fare_rules],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error in fare rule comparison: {str(e)}", exc_info=True)
            messages.error(request, 'Error comparing fare rules.')
            return redirect('flights:fare_rules_list')
    
    def get_rule_applicability(self, fare_rule):
        """Get rule applicability details"""
        applicability = {
            'dates': f"{fare_rule.travel_date_start} to {fare_rule.travel_date_end}",
            'advance_purchase': fare_rule.advance_purchase_days,
            'minimum_stay': fare_rule.minimum_stay_days,
            'maximum_stay': fare_rule.maximum_stay_days,
            'day_restrictions': fare_rule.day_restrictions,
            'time_restrictions': fare_rule.time_restrictions,
        }
        return applicability
    
    def create_comparison_matrix(self, comparison_data):
        """Create comparison matrix for fare rules"""
        if not comparison_data:
            return []
        
        # Define comparison categories
        categories = [
            'airline',
            'fare_basis',
            'cabin_class',
            'validity_period',
            'advance_purchase',
            'minimum_stay',
            'maximum_stay',
            'refundable',
            'changeable',
            'penalties',
            'baggage_allowance',
            'day_restrictions',
            'time_restrictions',
        ]
        
        matrix = []
        for category in categories:
            row = {'category': category, 'values': []}
            
            for data in comparison_data:
                fare_rule = data['rule']
                baggage_rules = data['baggage_rules']
                
                if category == 'airline':
                    value = f"{fare_rule.airline.code} - {fare_rule.airline.name}"
                elif category == 'fare_basis':
                    value = fare_rule.fare_basis
                elif category == 'cabin_class':
                    value = fare_rule.get_cabin_class_display()
                elif category == 'validity_period':
                    value = f"{fare_rule.travel_date_start} to {fare_rule.travel_date_end}"
                elif category == 'advance_purchase':
                    value = f"{fare_rule.advance_purchase_days} days" if fare_rule.advance_purchase_days else "None"
                elif category == 'minimum_stay':
                    value = f"{fare_rule.minimum_stay_days} days" if fare_rule.minimum_stay_days else "None"
                elif category == 'maximum_stay':
                    value = f"{fare_rule.maximum_stay_days} days" if fare_rule.maximum_stay_days else "Unlimited"
                elif category == 'refundable':
                    value = "Yes" if fare_rule.is_refundable else "No"
                elif category == 'changeable':
                    value = "Yes" if fare_rule.is_changeable else "No"
                elif category == 'penalties':
                    penalties = []
                    if fare_rule.cancellation_penalty:
                        penalties.append(f"Cancellation: {fare_rule.cancellation_penalty}")
                    if fare_rule.change_penalty:
                        penalties.append(f"Change: {fare_rule.change_penalty}")
                    if fare_rule.no_show_penalty:
                        penalties.append(f"No-show: {fare_rule.no_show_penalty}")
                    value = ", ".join(penalties) if penalties else "None"
                elif category == 'baggage_allowance':
                    if baggage_rules:
                        value = f"{baggage_rules.checked_pieces} checked, {baggage_rules.cabin_pieces} cabin"
                    else:
                        value = "Standard"
                elif category == 'day_restrictions':
                    value = fare_rule.day_restrictions or "None"
                elif category == 'time_restrictions':
                    value = fare_rule.time_restrictions or "None"
                else:
                    value = "N/A"
                
                row['values'].append(value)
            
            matrix.append(row)
        
        return matrix


class FareRuleParserView(LoginRequiredMixin, View):
    """Parse GDS fare rule text into structured format"""
    
    template_name = 'flights/fare_rules/fare_rule_parser.html'
    
    def get(self, request):
        return render(request, self.template_name)
    
    def post(self, request):
        try:
            rule_text = request.POST.get('rule_text', '').strip()
            airline_code = request.POST.get('airline_code', '').strip().upper()
            fare_basis = request.POST.get('fare_basis', '').strip().upper()
            
            if not rule_text:
                messages.error(request, 'Please enter fare rule text.')
                return render(request, self.template_name)
            
            # Initialize parser
            parser = FareRuleParser()
            
            # Parse rule text
            parsed_data = parser.parse(rule_text, airline_code, fare_basis)
            
            # Get airline info
            airline = None
            if airline_code:
                airline = Airline.objects.filter(code=airline_code).first()
            
            context = {
                'original_text': rule_text,
                'parsed_data': parsed_data,
                'airline': airline,
                'fare_basis': fare_basis,
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error parsing fare rule text: {str(e)}", exc_info=True)
            messages.error(request, f'Error parsing fare rule text: {str(e)}')
            return render(request, self.template_name)


class BaggageRulesView(LoginRequiredMixin, View):
    """View and search baggage rules"""
    
    template_name = 'flights/fare_rules/baggage_rules.html'
    
    def get(self, request):
        try:
            # Get filter parameters
            airline_filter = request.GET.get('airline', 'all')
            cabin_class_filter = request.GET.get('cabin_class', 'all')
            search_query = request.GET.get('q', '').strip()
            page_number = request.GET.get('page', 1)
            
            # Base queryset
            baggage_rules = BaggageRule.objects.select_related(
                'airline'
            ).order_by('airline__code', 'cabin_class')
            
            # Apply filters
            if airline_filter != 'all':
                baggage_rules = baggage_rules.filter(airline__code=airline_filter)
            
            if cabin_class_filter != 'all':
                baggage_rules = baggage_rules.filter(cabin_class=cabin_class_filter)
            
            if search_query:
                baggage_rules = baggage_rules.filter(
                    Q(airline__name__icontains=search_query) |
                    Q(airline__code__icontains=search_query) |
                    Q(fare_basis__icontains=search_query)
                )
            
            # Get statistics
            stats = self.get_baggage_rule_statistics(baggage_rules)
            
            # Pagination
            paginator = Paginator(baggage_rules, 20)
            page_obj = paginator.get_page(page_number)
            
            # Get airlines for filter
            airlines = Airline.objects.filter(is_active=True).order_by('name')
            
            context = {
                'page_obj': page_obj,
                'airlines': airlines,
                'airline_filter': airline_filter,
                'cabin_class_filter': cabin_class_filter,
                'search_query': search_query,
                'stats': stats,
                'cabin_classes': [
                    ('all', 'All Classes'),
                    ('economy', 'Economy'),
                    ('premium_economy', 'Premium Economy'),
                    ('business', 'Business'),
                    ('first', 'First Class'),
                ],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading baggage rules: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading baggage rules.')
            return render(request, self.template_name, {'page_obj': []})
    
    def get_baggage_rule_statistics(self, baggage_rules):
        """Calculate baggage rule statistics"""
        stats = {
            'total_rules': baggage_rules.count(),
            'by_airline': {},
            'by_cabin': {},
        }
        
        # Airline breakdown
        airline_counts = baggage_rules.values('airline__code', 'airline__name').annotate(count=Count('id'))
        stats['by_airline'] = {
            f"{item['airline__code']}": {
                'name': item['airline__name'],
                'count': item['count']
            }
            for item in airline_counts
        }
        
        # Cabin class breakdown
        cabin_counts = baggage_rules.values('cabin_class').annotate(count=Count('id'))
        stats['by_cabin'] = {item['cabin_class']: item['count'] for item in cabin_counts}
        
        return stats


class FareRuleExportView(LoginRequiredMixin, View):
    """Export fare rules to various formats"""
    
    def get(self, request):
        try:
            export_format = request.GET.get('format', 'excel')
            export_type = request.GET.get('type', 'all')
            
            # Get filter parameters
            airline_filter = request.GET.get('airline', 'all')
            cabin_class_filter = request.GET.get('cabin_class', 'all')
            status_filter = request.GET.get('status', 'active')
            
            # Build queryset
            fare_rules = FareRule.objects.select_related('airline')
            
            # Apply filters
            if airline_filter != 'all':
                fare_rules = fare_rules.filter(airline__code=airline_filter)
            
            if cabin_class_filter != 'all':
                fare_rules = fare_rules.filter(cabin_class=cabin_class_filter)
            
            if status_filter == 'active':
                today = timezone.now().date()
                fare_rules = fare_rules.filter(
                    travel_date_start__lte=today,
                    travel_date_end__gte=today,
                    is_active=True
                )
            elif status_filter == 'expired':
                today = timezone.now().date()
                fare_rules = fare_rules.filter(travel_date_end__lt=today)
            
            # Export based on format
            export_utils = ExportUtils()
            
            if export_format == 'excel':
                return export_utils.export_fare_rules_to_excel(fare_rules, export_type)
            elif export_format == 'csv':
                return export_utils.export_fare_rules_to_csv(fare_rules, export_type)
            elif export_format == 'pdf':
                return export_utils.export_fare_rules_to_pdf(fare_rules, export_type)
            else:
                messages.error(request, 'Invalid export format.')
                return redirect('flights:fare_rules_list')
                
        except Exception as e:
            logger.error(f"Error exporting fare rules: {str(e)}", exc_info=True)
            messages.error(request, 'Error exporting fare rules.')
            return redirect('flights:fare_rules_list')


class GDSFareRulesView(LoginRequiredMixin, View):
    """Fetch and display fare rules from GDS"""
    
    template_name = 'flights/fare_rules/gds_fare_rules.html'
    
    def get(self, request):
        try:
            # Get parameters
            origin = request.GET.get('origin', '').upper()
            destination = request.GET.get('destination', '').upper()
            airline = request.GET.get('airline', '').upper()
            fare_basis = request.GET.get('fare_basis', '').upper()
            travel_date = request.GET.get('travel_date', '')
            
            context = {
                'origin': origin,
                'destination': destination,
                'airline': airline,
                'fare_basis': fare_basis,
                'travel_date': travel_date,
                'results': None,
                'error': None,
            }
            
            # Check if search parameters are provided
            if origin and destination and travel_date:
                try:
                    # Initialize GDS service
                    gds_service = GDSFareService()
                    
                    # Fetch fare rules from GDS
                    results = gds_service.get_fare_rules(
                        origin=origin,
                        destination=destination,
                        airline=airline,
                        fare_basis=fare_basis,
                        travel_date=travel_date
                    )
                    
                    context['results'] = results
                    
                    # Save to database if requested
                    if 'save' in request.GET and results.get('success'):
                        self.save_gds_fare_rules(results, request.user)
                        
                except Exception as e:
                    logger.error(f"Error fetching GDS fare rules: {str(e)}", exc_info=True)
                    context['error'] = str(e)
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error in GDS fare rules view: {str(e)}", exc_info=True)
            messages.error(request, 'Error accessing GDS fare rules.')
            return render(request, self.template_name)
    
    def save_gds_fare_rules(self, results, user):
        """Save GDS fare rules to database"""
        try:
            fare_service = FareService()
            
            for fare_rule_data in results.get('fare_rules', []):
                fare_service.create_or_update_fare_rule(
                    fare_rule_data=fare_rule_data,
                    created_by=user
                )
            
            messages.success(request, f"Saved {len(results.get('fare_rules', []))} fare rules to database.")
            
        except Exception as e:
            logger.error(f"Error saving GDS fare rules: {str(e)}")
            messages.error(request, 'Error saving fare rules to database.')


class FareRuleCategoriesView(LoginRequiredMixin, View):
    """View fare rule categories and their descriptions"""
    
    template_name = 'flights/fare_rules/fare_rule_categories.html'
    
    def get(self, request):
        try:
            # Define standard fare rule categories
            categories = [
                {
                    'code': 'MIN',
                    'name': 'Minimum Stay',
                    'description': 'Specifies the minimum number of days that must elapse between departure and return.',
                    'arabic_name': 'الإقامة الدنيا',
                    'examples': ['MIN STAY 3 DAYS', 'MIN STAY SAT NIGHT'],
                },
                {
                    'code': 'MAX',
                    'name': 'Maximum Stay',
                    'description': 'Specifies the maximum number of days allowed between departure and return.',
                    'arabic_name': 'الإقامة القصوى',
                    'examples': ['MAX STAY 30 DAYS', 'MAX STAY 3 MONTHS'],
                },
                {
                    'code': 'PEN',
                    'name': 'Penalties',
                    'description': 'Specifies penalties for changes, cancellations, and no-shows.',
                    'arabic_name': 'الغرامات',
                    'examples': ['CANCELLATION FEE SAR 500', 'CHANGE FEE SAR 300', 'NO SHOW FEE 100%'],
                },
                {
                    'code': 'COM',
                    'name': 'Combinations',
                    'description': 'Rules about combining fares with other fares or tickets.',
                    'arabic_name': 'التوليفات',
                    'examples': ['COMBINABLE WITH OTHER FARES', 'END-ON-END PROHIBITED'],
                },
                {
                    'code': 'BLK',
                    'name': 'Blackout Dates',
                    'description': 'Dates when the fare cannot be used.',
                    'arabic_name': 'أيام الحظر',
                    'examples': ['NOT VALID 24DEC-02JAN', 'BLACKOUT DATES APPLY'],
                },
                {
                    'code': 'RES',
                    'name': 'Reservations',
                    'description': 'Rules about reservations, ticketing deadlines, and waitlisting.',
                    'arabic_name': 'الحجوزات',
                    'examples': ['RESERVATIONS REQUIRED', 'TICKET BY 24HOURS'],
                },
                {
                    'code': 'TKT',
                    'name': 'Ticketing',
                    'description': 'Rules about ticketing, endorsements, and restrictions.',
                    'arabic_name': 'التذاكر',
                    'examples': ['TICKETING DEADLINE 7 DAYS', 'ENDORSEMENTS NOT PERMITTED'],
                },
                {
                    'code': 'CHD',
                    'name': 'Children',
                    'description': 'Rules and discounts applicable to child passengers.',
                    'arabic_name': 'الأطفال',
                    'examples': ['CHILD DISCOUNT 25%', 'CHILD 2-11 YEARS'],
                },
                {
                    'code': 'INF',
                    'name': 'Infants',
                    'description': 'Rules and discounts applicable to infant passengers.',
                    'arabic_name': 'الرضع',
                    'examples': ['INFANT DISCOUNT 90%', 'INFANT UNDER 2 YEARS'],
                },
                {
                    'code': 'MIL',
                    'name': 'Military',
                    'description': 'Special fares and rules for military personnel.',
                    'arabic_name': 'العسكريين',
                    'examples': ['MILITARY DISCOUNT 10%', 'MILITARY ID REQUIRED'],
                },
                {
                    'code': 'SRC',
                    'name': 'Senior Citizen',
                    'description': 'Special fares and rules for senior citizens.',
                    'arabic_name': 'كبار السن',
                    'examples': ['SENIOR DISCOUNT 15%', 'AGE 60+ REQUIRED'],
                },
                {
                    'code': 'GRP',
                    'name': 'Group',
                    'description': 'Rules for group bookings and discounts.',
                    'arabic_name': 'المجموعات',
                    'examples': ['GROUP MIN 10 PAX', 'GROUP DISCOUNT 20%'],
                },
            ]
            
            # Get category statistics
            category_stats = FareRule.objects.values('category').annotate(
                count=Count('id'),
                airlines=Count('airline', distinct=True)
            ).order_by('category')
            
            stats_dict = {item['category']: item for item in category_stats}
            
            # Add statistics to categories
            for category in categories:
                stats = stats_dict.get(category['code'], {'count': 0, 'airlines': 0})
                category['count'] = stats['count']
                category['airlines'] = stats['airlines']
            
            context = {
                'categories': categories,
                'total_rules': FareRule.objects.count(),
                'total_airlines': Airline.objects.filter(is_active=True).count(),
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading fare rule categories: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading fare rule categories.')
            return render(request, self.template_name, {'categories': []})


class FareRuleValidatorView(LoginRequiredMixin, View):
    """Validate fare rules against booking criteria"""
    
    template_name = 'flights/fare_rules/fare_rule_validator.html'
    
    def get(self, request):
        return render(request, self.template_name)
    
    def post(self, request):
        try:
            # Get validation criteria
            origin = request.POST.get('origin', '').upper()
            destination = request.POST.get('destination', '').upper()
            travel_date = request.POST.get('travel_date', '')
            return_date = request.POST.get('return_date', '')
            cabin_class = request.POST.get('cabin_class', 'economy')
            passenger_type = request.POST.get('passenger_type', 'ADT')
            airline = request.POST.get('airline', '').upper()
            
            if not all([origin, destination, travel_date]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, self.template_name)
            
            # Parse dates
            try:
                travel_date_obj = datetime.strptime(travel_date, '%Y-%m-%d').date()
                return_date_obj = datetime.strptime(return_date, '%Y-%m-%d').date() if return_date else None
            except ValueError:
                messages.error(request, 'Invalid date format. Use YYYY-MM-DD.')
                return render(request, self.template_name)
            
            # Initialize fare service
            fare_service = FareService()
            
            # Validate fare rules
            validation_results = fare_service.validate_fare_rules(
                origin=origin,
                destination=destination,
                travel_date=travel_date_obj,
                return_date=return_date_obj,
                cabin_class=cabin_class,
                passenger_type=passenger_type,
                airline=airline
            )
            
            # Get applicable fare rules
            applicable_rules = fare_service.get_applicable_fare_rules(
                origin=origin,
                destination=destination,
                travel_date=travel_date_obj,
                cabin_class=cabin_class,
                airline=airline
            )
            
            context = {
                'validation_criteria': {
                    'origin': origin,
                    'destination': destination,
                    'travel_date': travel_date,
                    'return_date': return_date,
                    'cabin_class': cabin_class,
                    'passenger_type': passenger_type,
                    'airline': airline,
                },
                'validation_results': validation_results,
                'applicable_rules': applicable_rules,
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error in fare rule validation: {str(e)}", exc_info=True)
            messages.error(request, f'Error validating fare rules: {str(e)}')
            return render(request, self.template_name)


# API Views for AJAX operations

@method_decorator(csrf_exempt, name='dispatch')
class FareRuleSearchAPI(View, LoginRequiredMixin):
    """API endpoint for fare rule search"""
    
    def get(self, request):
        try:
            search_term = request.GET.get('q', '').strip()
            airline = request.GET.get('airline', '').strip()
            
            if len(search_term) < 2:
                return JsonResponse({'results': []})
            
            # Search fare rules
            fare_rules = FareRule.objects.select_related('airline')
            
            if airline:
                fare_rules = fare_rules.filter(airline__code=airline)
            
            fare_rules = fare_rules.filter(
                Q(fare_basis__icontains=search_term) |
                Q(rule_text__icontains=search_term) |
                Q(rule_number__icontains=search_term)
            )[:10]
            
            results = []
            for rule in fare_rules:
                results.append({
                    'id': str(rule.id),
                    'text': f"{rule.airline.code} {rule.fare_basis} - {rule.category}",
                    'airline': rule.airline.code,
                    'fare_basis': rule.fare_basis,
                    'category': rule.get_category_display(),
                })
            
            return JsonResponse({'results': results})
            
        except Exception as e:
            logger.error(f"Error in fare rule search API: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class FareRuleDetailAPI(View, LoginRequiredMixin):
    """API endpoint for fare rule details"""
    
    def get(self, request, rule_id):
        try:
            fare_rule = get_object_or_404(FareRule.objects.select_related('airline'), id=rule_id)
            
            data = {
                'id': str(fare_rule.id),
                'airline': {
                    'code': fare_rule.airline.code,
                    'name': fare_rule.airline.name,
                },
                'fare_basis': fare_rule.fare_basis,
                'cabin_class': fare_rule.cabin_class,
                'category': fare_rule.get_category_display(),
                'rule_text': fare_rule.rule_text,
                'rule_text_ar': fare_rule.rule_text_ar,
                'applicability': {
                    'travel_dates': {
                        'start': fare_rule.travel_date_start.isoformat() if fare_rule.travel_date_start else None,
                        'end': fare_rule.travel_date_end.isoformat() if fare_rule.travel_date_end else None,
                    },
                    'advance_purchase': fare_rule.advance_purchase_days,
                    'minimum_stay': fare_rule.minimum_stay_days,
                    'maximum_stay': fare_rule.maximum_stay_days,
                },
                'penalties': {
                    'cancellation': fare_rule.cancellation_penalty,
                    'change': fare_rule.change_penalty,
                    'no_show': fare_rule.no_show_penalty,
                },
                'restrictions': {
                    'is_refundable': fare_rule.is_refundable,
                    'is_changeable': fare_rule.is_changeable,
                    'day_restrictions': fare_rule.day_restrictions,
                    'time_restrictions': fare_rule.time_restrictions,
                },
            }
            
            return JsonResponse(data)
            
        except Exception as e:
            logger.error(f"Error in fare rule detail API: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class BaggageRuleAPI(View, LoginRequiredMixin):
    """API endpoint for baggage rules"""
    
    def get(self, request):
        try:
            airline = request.GET.get('airline', '').strip().upper()
            cabin_class = request.GET.get('cabin_class', 'economy').strip()
            
            if not airline:
                return JsonResponse({'error': 'Airline code is required'}, status=400)
            
            baggage_rule = BaggageRule.objects.filter(
                airline__code=airline,
                cabin_class=cabin_class
            ).first()
            
            if not baggage_rule:
                # Return default baggage rules
                data = {
                    'checked_pieces': 1,
                    'checked_weight_kg': 23,
                    'cabin_pieces': 1,
                    'cabin_weight_kg': 7,
                    'is_default': True,
                }
            else:
                data = {
                    'checked_pieces': baggage_rule.checked_pieces,
                    'checked_weight_kg': float(baggage_rule.checked_weight_kg) if baggage_rule.checked_weight_kg else 23,
                    'checked_dimensions_cm': baggage_rule.checked_dimensions_cm,
                    'cabin_pieces': baggage_rule.cabin_pieces,
                    'cabin_weight_kg': float(baggage_rule.cabin_weight_kg) if baggage_rule.cabin_weight_kg else 7,
                    'cabin_dimensions_cm': baggage_rule.cabin_dimensions_cm,
                    'sports_equipment': baggage_rule.sports_equipment,
                    'musical_instruments': baggage_rule.musical_instruments,
                    'pets_allowed': baggage_rule.pets_allowed,
                    'excess_price_per_kg': float(baggage_rule.excess_price_per_kg) if baggage_rule.excess_price_per_kg else None,
                    'excess_price_per_piece': float(baggage_rule.excess_price_per_piece) if baggage_rule.excess_price_per_piece else None,
                    'is_default': False,
                }
            
            return JsonResponse(data)
            
        except Exception as e:
            logger.error(f"Error in baggage rule API: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class FareRuleValidationAPI(View, LoginRequiredMixin):
    """API endpoint for fare rule validation"""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            # Get validation parameters
            fare_rule_id = data.get('fare_rule_id')
            travel_date = data.get('travel_date')
            return_date = data.get('return_date')
            passenger_type = data.get('passenger_type', 'ADT')
            
            if not fare_rule_id or not travel_date:
                return JsonResponse({'error': 'Missing required parameters'}, status=400)
            
            # Get fare rule
            fare_rule = get_object_or_404(FareRule, id=fare_rule_id)
            
            # Parse dates
            travel_date_obj = datetime.strptime(travel_date, '%Y-%m-%d').date()
            return_date_obj = datetime.strptime(return_date, '%Y-%m-%d').date() if return_date else None
            
            # Validate fare rule
            fare_service = FareService()
            validation_result = fare_service.validate_single_fare_rule(
                fare_rule=fare_rule,
                travel_date=travel_date_obj,
                return_date=return_date_obj,
                passenger_type=passenger_type
            )
            
            return JsonResponse(validation_result)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except ValueError as e:
            return JsonResponse({'error': f'Invalid date format: {str(e)}'}, status=400)
        except Exception as e:
            logger.error(f"Error in fare rule validation API: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


class FareRulesDashboardView(LoginRequiredMixin, View):
    """Fare rules dashboard with analytics"""
    
    template_name = 'flights/fare_rules/fare_rules_dashboard.html'
    
    def get(self, request):
        try:
            # Get time period
            time_period = request.GET.get('period', '30d')
            
            # Calculate date range
            today = timezone.now().date()
            if time_period == '7d':
                start_date = today - timedelta(days=7)
            elif time_period == '30d':
                start_date = today - timedelta(days=30)
            elif time_period == '90d':
                start_date = today - timedelta(days=90)
            else:
                start_date = today - timedelta(days=30)
            
            # Get statistics
            stats = self.get_dashboard_statistics(start_date, today)
            
            # Get trending fare rules
            trending_rules = self.get_trending_fare_rules(start_date, today)
            
            # Get airline performance
            airline_performance = self.get_airline_performance(start_date, today)
            
            # Get rule category distribution
            category_distribution = self.get_category_distribution()
            
            context = {
                'stats': stats,
                'trending_rules': trending_rules,
                'airline_performance': airline_performance,
                'category_distribution': category_distribution,
                'time_period': time_period,
                'period_options': [
                    ('7d', 'Last 7 Days'),
                    ('30d', 'Last 30 Days'),
                    ('90d', 'Last 90 Days'),
                ],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading fare rules dashboard: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading dashboard.')
            return render(request, self.template_name)
    
    def get_dashboard_statistics(self, start_date, end_date):
        """Get dashboard statistics"""
        stats = {}
        
        # Total fare rules
        stats['total_rules'] = FareRule.objects.count()
        
        # Active fare rules
        today = timezone.now().date()
        stats['active_rules'] = FareRule.objects.filter(
            travel_date_start__lte=today,
            travel_date_end__gte=today,
            is_active=True
        ).count()
        
        # New fare rules in period
        stats['new_rules'] = FareRule.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).count()
        
        # Expired fare rules in period
        stats['expired_rules'] = FareRule.objects.filter(
            travel_date_end__gte=start_date,
            travel_date_end__lte=end_date
        ).count()
        
        # Airline count
        stats['airline_count'] = Airline.objects.filter(
            fare_rules__isnull=False
        ).distinct().count()
        
        # Most used fare rules
        most_used = Booking.objects.filter(
            itinerary__segments__fare_basis__isnull=False,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).values('itinerary__segments__fare_basis').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        if most_used:
            stats['most_used_fare_basis'] = most_used['itinerary__segments__fare_basis']
            stats['most_used_count'] = most_used['count']
        else:
            stats['most_used_fare_basis'] = 'N/A'
            stats['most_used_count'] = 0
        
        return stats
    
    def get_trending_fare_rules(self, start_date, end_date):
        """Get trending fare rules"""
        trending = FareRule.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).select_related('airline').order_by('-created_at')[:10]
        
        return [
            {
                'fare_basis': rule.fare_basis,
                'airline': rule.airline.code,
                'cabin_class': rule.cabin_class,
                'created_at': rule.created_at.strftime('%Y-%m-%d'),
                'valid_until': rule.travel_date_end.strftime('%Y-%m-%d') if rule.travel_date_end else 'N/A',
            }
            for rule in trending
        ]
    
    def get_airline_performance(self, start_date, end_date):
        """Get airline performance metrics"""
        performance = []
        
        airlines = Airline.objects.filter(
            fare_rules__isnull=False
        ).distinct().order_by('code')
        
        for airline in airlines[:10]:  # Limit to top 10
            fare_rules_count = airline.fare_rules.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).count()
            
            bookings_count = Booking.objects.filter(
                itinerary__segments__airline=airline,
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).count()
            
            if fare_rules_count > 0 or bookings_count > 0:
                performance.append({
                    'airline': airline.code,
                    'name': airline.name,
                    'fare_rules_count': fare_rules_count,
                    'bookings_count': bookings_count,
                    'performance_score': (bookings_count * 10) + (fare_rules_count * 5),
                })
        
        # Sort by performance score
        performance.sort(key=lambda x: x['performance_score'], reverse=True)
        
        return performance
    
    def get_category_distribution(self):
        """Get rule category distribution"""
        distribution = FareRule.objects.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return [
            {
                'category': item['category'],
                'count': item['count'],
                'percentage': (item['count'] / FareRule.objects.count() * 100) if FareRule.objects.count() > 0 else 0,
            }
            for item in distribution
        ]


class FareRulesImportView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Import fare rules from various sources"""
    
    template_name = 'flights/fare_rules/fare_rules_import.html'
    
    def test_func(self):
        return self.request.user.user_type in ['admin', 'super_agent']
    
    def get(self, request):
        return render(request, self.template_name)
    
    def post(self, request):
        try:
            import_type = request.POST.get('import_type')
            import_file = request.FILES.get('import_file')
            import_text = request.POST.get('import_text', '').strip()
            airline_code = request.POST.get('airline_code', '').strip().upper()
            
            if not airline_code:
                messages.error(request, 'Airline code is required.')
                return render(request, self.template_name)
            
            # Get airline
            airline = get_object_or_404(Airline, code=airline_code)
            
            # Process import based on type
            if import_type == 'gds_text':
                if not import_text:
                    messages.error(request, 'GDS text is required.')
                    return render(request, self.template_name)
                
                result = self.import_from_gds_text(import_text, airline, request.user)
                
            elif import_type == 'csv_file':
                if not import_file:
                    messages.error(request, 'CSV file is required.')
                    return render(request, self.template_name)
                
                result = self.import_from_csv(import_file, airline, request.user)
                
            elif import_type == 'excel_file':
                if not import_file:
                    messages.error(request, 'Excel file is required.')
                    return render(request, self.template_name)
                
                result = self.import_from_excel(import_file, airline, request.user)
                
            else:
                messages.error(request, 'Invalid import type.')
                return render(request, self.template_name)
            
            context = {
                'result': result,
                'airline': airline,
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error importing fare rules: {str(e)}", exc_info=True)
            messages.error(request, f'Error importing fare rules: {str(e)}')
            return render(request, self.template_name)
    
    def import_from_gds_text(self, gds_text, airline, user):
        """Import fare rules from GDS text"""
        try:
            # Initialize parser
            parser = FareRuleParser()
            
            # Parse GDS text
            parsed_rules = parser.parse_bulk(gds_text, airline.code)
            
            # Import fare rules
            fare_service = FareService()
            result = fare_service.import_fare_rules(
                fare_rules_data=parsed_rules,
                airline=airline,
                created_by=user
            )
            
            return {
                'success': True,
                'message': f"Successfully imported {result.get('imported_count', 0)} fare rules.",
                'details': result,
            }
            
        except Exception as e:
            logger.error(f"Error importing from GDS text: {str(e)}")
            return {
                'success': False,
                'message': f"Error importing from GDS text: {str(e)}",
            }
    
    def import_from_csv(self, csv_file, airline, user):
        """Import fare rules from CSV file"""
        try:
            import csv
            import io
            
            # Read CSV file
            csv_text = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_text))
            
            # Process rows
            fare_rules_data = []
            for row in csv_reader:
                fare_rules_data.append({
                    'fare_basis': row.get('fare_basis', ''),
                    'category': row.get('category', ''),
                    'rule_text': row.get('rule_text', ''),
                    'rule_text_ar': row.get('rule_text_ar', ''),
                    'travel_date_start': row.get('travel_date_start'),
                    'travel_date_end': row.get('travel_date_end'),
                    'cabin_class': row.get('cabin_class', 'economy'),
                })
            
            # Import fare rules
            fare_service = FareService()
            result = fare_service.import_fare_rules(
                fare_rules_data=fare_rules_data,
                airline=airline,
                created_by=user
            )
            
            return {
                'success': True,
                'message': f"Successfully imported {result.get('imported_count', 0)} fare rules.",
                'details': result,
            }
            
        except Exception as e:
            logger.error(f"Error importing from CSV: {str(e)}")
            return {
                'success': False,
                'message': f"Error importing from CSV: {str(e)}",
            }
    
    def import_from_excel(self, excel_file, airline, user):
        """Import fare rules from Excel file"""
        try:
            import pandas as pd
            import io
            
            # Read Excel file
            df = pd.read_excel(excel_file)
            
            # Convert to list of dictionaries
            fare_rules_data = df.to_dict('records')
            
            # Import fare rules
            fare_service = FareService()
            result = fare_service.import_fare_rules(
                fare_rules_data=fare_rules_data,
                airline=airline,
                created_by=user
            )
            
            return {
                'success': True,
                'message': f"Successfully imported {result.get('imported_count', 0)} fare rules.",
                'details': result,
            }
            
        except Exception as e:
            logger.error(f"Error importing from Excel: {str(e)}")
            return {
                'success': False,
                'message': f"Error importing from Excel: {str(e)}",
            }


class FareRulesCleanupView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Cleanup expired and duplicate fare rules"""
    
    template_name = 'flights/fare_rules/fare_rules_cleanup.html'
    
    def test_func(self):
        return self.request.user.user_type in ['admin', 'super_agent']
    
    def get(self, request):
        try:
            # Get cleanup statistics
            stats = self.get_cleanup_statistics()
            
            context = {
                'stats': stats,
                'cleanup_options': [
                    ('expired', 'Expired Fare Rules'),
                    ('duplicate', 'Duplicate Fare Rules'),
                    ('inactive', 'Inactive Fare Rules'),
                    ('all', 'All Cleanup Tasks'),
                ],
            }
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error loading cleanup view: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading cleanup page.')
            return render(request, self.template_name)
    
    def post(self, request):
        try:
            cleanup_type = request.POST.get('cleanup_type')
            
            if not cleanup_type:
                messages.error(request, 'Please select a cleanup type.')
                return redirect('flights:fare_rules_cleanup')
            
            # Perform cleanup
            fare_service = FareService()
            result = fare_service.cleanup_fare_rules(cleanup_type, request.user)
            
            messages.success(request, result.get('message', 'Cleanup completed.'))
            
            return redirect('flights:fare_rules_cleanup')
            
        except Exception as e:
            logger.error(f"Error performing cleanup: {str(e)}", exc_info=True)
            messages.error(request, f'Error performing cleanup: {str(e)}')
            return redirect('flights:fare_rules_cleanup')
    
    def get_cleanup_statistics(self):
        """Get cleanup statistics"""
        today = timezone.now().date()
        
        stats = {
            'expired_rules': FareRule.objects.filter(
                travel_date_end__lt=today
            ).count(),
            'inactive_rules': FareRule.objects.filter(
                is_active=False
            ).count(),
            'duplicate_rules': self.get_duplicate_count(),
            'total_cleanup': 0,
        }
        
        stats['total_cleanup'] = (
            stats['expired_rules'] +
            stats['inactive_rules'] +
            stats['duplicate_rules']
        )
        
        return stats
    
    def get_duplicate_count(self):
        """Get count of duplicate fare rules"""
        # Find fare rules with same airline, fare_basis, and category
        duplicates = FareRule.objects.values(
            'airline', 'fare_basis', 'category'
        ).annotate(
            count=Count('id')
        ).filter(
            count__gt=1
        )
        
        duplicate_count = 0
        for dup in duplicates:
            duplicate_count += dup['count'] - 1
        
        return duplicate_count