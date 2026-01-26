"""
Reporting and Analytics Views for B2B Travel Platform
Production Ready - Final Version
Integrated with Travelport Galileo GDS
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import (
    Q, Count, Sum, Avg, F, Value, Case, When,
    IntegerField, DecimalField, DateField,
    Subquery, OuterRef, Prefetch, Window, Func
)
from django.db.models.functions import (
    TruncDate, TruncMonth, TruncQuarter, TruncYear,
    Extract, ExtractYear, ExtractMonth,
    Coalesce, Concat, Cast
)
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.db import transaction, connection
from django.core.cache import cache
import json
import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
import csv
import io
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# Optional pandas import
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from io import BytesIO
import base64
import calendar

# Optional imports for models
try:
    from flights.models import (
        Booking, Ticket, Payment, CommissionTransaction, Refund,
        FlightSearch, FlightItinerary, Passenger, AncillaryBooking,
        Airline, Airport, AgentHierarchy,
        BookingHistory, PNR, EMD
    )
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False

# Optional imports for forms
try:
    from flights.forms import (
        SalesReportForm, AgentPerformanceForm, AirlineReportForm,
        RevenueReportForm, BookingAnalysisForm, CustomReportForm
    )
    FORMS_AVAILABLE = True
except ImportError:
    FORMS_AVAILABLE = False

# Optional imports for services
try:
    from flights.services.reporting_service import (
        SalesReportingService, AgentPerformanceService,
        AirlineAnalysisService, RevenueAnalyticsService,
        BookingAnalyticsService, CustomReportService
    )
except ImportError:
    SalesReportingService = None
    AgentPerformanceService = None
    AirlineAnalysisService = None
    RevenueAnalyticsService = None
    BookingAnalyticsService = None
    CustomReportService = None

try:
    from flights.services.export_service import ReportExportService
except ImportError:
    ReportExportService = None

try:
    from flights.utils.charts import ChartGenerator
except ImportError:
    ChartGenerator = None

try:
    from flights.utils.validators import ReportValidator
except ImportError:
    ReportValidator = None

try:
    from flights.utils.permissions import ReportPermission
except ImportError:
    ReportPermission = None

try:
    from flights.utils.cache import ReportCache
except ImportError:
    ReportCache = None

logger = logging.getLogger(__name__)


# ==============================================
# BASE REPORTING VIEWS
# ==============================================

class BaseReportingView(LoginRequiredMixin, UserPassesTestMixin):
    """Base view for all reporting views"""
    
    def test_func(self):
        """Check if user has reporting access"""
        return ReportPermission.can_access_reports(self.request.user)
    
    def get_date_range(self, date_from=None, date_to=None):
        """Get date range with default values"""
        if not date_from or not date_to:
            # Default to last 30 days
            date_to = timezone.now().date()
            date_from = date_to - timedelta(days=30)
        else:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            except ValueError:
                date_to = timezone.now().date()
                date_from = date_to - timedelta(days=30)
        
        # Ensure date_to is not in the future
        if date_to > timezone.now().date():
            date_to = timezone.now().date()
        
        return date_from, date_to
    
    def get_report_context(self, title, data=None, filters=None):
        """Get common report context"""
        user = self.request.user
        context = {
            'title': title,
            'user': user,
            'user_type': user.user_type,
            'company_name': user.profile.company_name if hasattr(user, 'profile') else '',
            'today': timezone.now().date(),
            'filters': filters or {},
            'data': data or {},
            'can_export': ReportPermission.can_export_reports(user),
            'can_schedule': ReportPermission.can_schedule_reports(user),
            'report_types': self.get_report_types(user),
        }
        return context


# ==============================================
# SALES REPORTING VIEWS
# ==============================================

class SalesDashboardView(BaseReportingView, View):
    """Sales Dashboard - Main reporting interface"""
    
    template_name = 'flights/reports/sales_dashboard.html'
    
    def get(self, request):
        try:
            # Get date range
            date_from = request.GET.get('date_from', '')
            date_to = request.GET.get('date_to', '')
            date_from, date_to = self.get_date_range(date_from, date_to)
            
            # Initialize services
            sales_service = SalesReportingService()
            
            # Get dashboard metrics
            metrics = sales_service.get_dashboard_metrics(
                user=request.user,
                date_from=date_from,
                date_to=date_to
            )
            
            # Get recent bookings
            recent_bookings = Booking.objects.filter(
                agent=request.user,
                created_at__date__range=[date_from, date_to]
            ).select_related('itinerary')[:10]
            
            # Get top airlines
            top_airlines = sales_service.get_top_airlines(
                user=request.user,
                date_from=date_from,
                date_to=date_to,
                limit=5
            )
            
            # Get revenue trends
            revenue_trends = sales_service.get_revenue_trends(
                user=request.user,
                date_from=date_from - timedelta(days=90),
                date_to=date_to,
                period='weekly'
            )
            
            context = self.get_report_context(
                title='Sales Dashboard',
                data={
                    'metrics': metrics,
                    'recent_bookings': recent_bookings,
                    'top_airlines': top_airlines,
                    'revenue_trends': revenue_trends,
                    'date_from': date_from,
                    'date_to': date_to,
                },
                filters={
                    'date_from': date_from,
                    'date_to': date_to,
                }
            )
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Sales dashboard error: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading sales dashboard.')
            return render(request, self.template_name, {
                'error': str(e),
                'title': 'Sales Dashboard'
            })


class SalesReportView(BaseReportingView, View):
    """Sales Report - Detailed sales analysis"""
    
    template_name = 'flights/reports/sales_report.html'
    
    def get(self, request):
        try:
            form = SalesReportForm(request.GET or None)
            report_data = None
            
            if form.is_valid():
                # Get form data
                date_from = form.cleaned_data['date_from']
                date_to = form.cleaned_data['date_to']
                report_type = form.cleaned_data['report_type']
                airline = form.cleaned_data['airline']
                agent_id = form.cleaned_data['agent_id']
                group_by = form.cleaned_data['group_by']
                
                # Initialize service
                sales_service = SalesReportingService()
                
                # Generate report
                if report_type == 'daily':
                    report_data = sales_service.generate_daily_sales_report(
                        date_from=date_from,
                        date_to=date_to,
                        airline_code=airline.code if airline else None,
                        agent_id=agent_id if agent_id else None,
                        group_by=group_by
                    )
                elif report_type == 'airline':
                    report_data = sales_service.generate_airline_sales_report(
                        date_from=date_from,
                        date_to=date_to,
                        agent_id=agent_id if agent_id else None
                    )
                elif report_type == 'agent':
                    if not ReportPermission.can_view_agent_reports(request.user):
                        raise PermissionDenied("You don't have permission to view agent reports")
                    report_data = sales_service.generate_agent_sales_report(
                        date_from=date_from,
                        date_to=date_to
                    )
                elif report_type == 'route':
                    report_data = sales_service.generate_route_sales_report(
                        date_from=date_from,
                        date_to=date_to,
                        agent_id=agent_id if agent_id else None
                    )
            
            context = self.get_report_context(
                title='Sales Report',
                data={'report_data': report_data},
                filters={'form': form}
            )
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect('flights:reports_dashboard')
        except Exception as e:
            logger.error(f"Sales report error: {str(e)}", exc_info=True)
            messages.error(request, 'Error generating sales report.')
            return render(request, self.template_name, {
                'error': str(e),
                'title': 'Sales Report'
            })


class RevenueReportView(BaseReportingView, View):
    """Revenue Report - Financial analysis"""
    
    template_name = 'flights/reports/revenue_report.html'
    
    def get(self, request):
        try:
            form = RevenueReportForm(request.GET or None)
            report_data = None
            
            if form.is_valid():
                # Get form data
                date_from = form.cleaned_data['date_from']
                date_to = form.cleaned_data['date_to']
                revenue_type = form.cleaned_data['revenue_type']
                include_ancillary = form.cleaned_data['include_ancillary']
                include_taxes = form.cleaned_data['include_taxes']
                
                # Initialize service
                revenue_service = RevenueAnalyticsService()
                
                # Generate report
                report_data = revenue_service.generate_revenue_report(
                    date_from=date_from,
                    date_to=date_to,
                    revenue_type=revenue_type,
                    include_ancillary=include_ancillary,
                    include_taxes=include_taxes,
                    user=request.user
                )
            
            context = self.get_report_context(
                title='Revenue Report',
                data={'report_data': report_data},
                filters={'form': form}
            )
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Revenue report error: {str(e)}", exc_info=True)
            messages.error(request, 'Error generating revenue report.')
            return render(request, self.template_name, {
                'error': str(e),
                'title': 'Revenue Report'
            })


class CommissionReportView(BaseReportingView, View):
    """Commission Report - Commission earnings analysis"""
    
    template_name = 'flights/reports/commission_report.html'
    
    def get(self, request):
        try:
            # Get date range
            date_from = request.GET.get('date_from', '')
            date_to = request.GET.get('date_to', '')
            date_from, date_to = self.get_date_range(date_from, date_to)
            
            # Get commission data
            commission_data = self.get_commission_data(request.user, date_from, date_to)
            
            # Get commission trends
            commission_trends = self.get_commission_trends(request.user, date_from, date_to)
            
            # Get top commission airlines
            top_airlines = self.get_top_commission_airlines(request.user, date_from, date_to)
            
            context = self.get_report_context(
                title='Commission Report',
                data={
                    'commission_data': commission_data,
                    'commission_trends': commission_trends,
                    'top_airlines': top_airlines,
                    'date_from': date_from,
                    'date_to': date_to,
                },
                filters={
                    'date_from': date_from,
                    'date_to': date_to,
                }
            )
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Commission report error: {str(e)}", exc_info=True)
            messages.error(request, 'Error generating commission report.')
            return render(request, self.template_name, {
                'error': str(e),
                'title': 'Commission Report'
            })
    
    def get_commission_data(self, user, date_from, date_to):
        """Get commission data for user"""
        # Base queryset
        if user.user_type == 'admin':
            commissions = CommissionTransaction.objects.filter(
                transaction_date__date__range=[date_from, date_to]
            )
        else:
            commissions = CommissionTransaction.objects.filter(
                agent=user,
                transaction_date__date__range=[date_from, date_to]
            )
        
        # Aggregate data
        total_commission = commissions.aggregate(
            total=Sum('commission_amount'),
            count=Count('id'),
            average=Avg('commission_amount')
        )
        
        # By status
        by_status = commissions.values('status').annotate(
            total=Sum('commission_amount'),
            count=Count('id')
        ).order_by('-total')
        
        # By airline
        by_airline = commissions.values('airline__code', 'airline__name').annotate(
            total=Sum('commission_amount'),
            count=Count('id')
        ).order_by('-total')
        
        return {
            'summary': total_commission,
            'by_status': list(by_status),
            'by_airline': list(by_airline),
            'total_records': commissions.count(),
        }
    
    def get_commission_trends(self, user, date_from, date_to):
        """Get commission trends over time"""
        # Calculate number of days
        days_diff = (date_to - date_from).days
        
        if days_diff <= 30:
            # Daily trends
            trunc_func = TruncDate('transaction_date')
        elif days_diff <= 90:
            # Weekly trends
            trunc_func = TruncDate('transaction_date')
        else:
            # Monthly trends
            trunc_func = TruncMonth('transaction_date')
        
        # Base queryset
        if user.user_type == 'admin':
            commissions = CommissionTransaction.objects.filter(
                transaction_date__date__range=[date_from, date_to]
            )
        else:
            commissions = CommissionTransaction.objects.filter(
                agent=user,
                transaction_date__date__range=[date_from, date_to]
            )
        
        # Group by time period
        trends = commissions.annotate(
            period=trunc_func
        ).values('period').annotate(
            total_commission=Sum('commission_amount'),
            total_transactions=Count('id'),
            average_commission=Avg('commission_amount')
        ).order_by('period')
        
        return list(trends)
    
    def get_top_commission_airlines(self, user, date_from, date_to, limit=10):
        """Get top airlines by commission"""
        # Base queryset
        if user.user_type == 'admin':
            commissions = CommissionTransaction.objects.filter(
                transaction_date__date__range=[date_from, date_to]
            )
        else:
            commissions = CommissionTransaction.objects.filter(
                agent=user,
                transaction_date__date__range=[date_from, date_to]
            )
        
        # Get top airlines
        top_airlines = commissions.values(
            'airline__code',
            'airline__name'
        ).annotate(
            total_commission=Sum('commission_amount'),
            total_bookings=Count('booking', distinct=True),
            average_commission=Avg('commission_amount')
        ).order_by('-total_commission')[:limit]
        
        return list(top_airlines)


# ==============================================
# PERFORMANCE REPORTING VIEWS
# ==============================================

class AgentPerformanceView(BaseReportingView, View):
    """Agent Performance Report - Individual and team performance"""
    
    template_name = 'flights/reports/agent_performance.html'
    
    def get(self, request):
        try:
            form = AgentPerformanceForm(request.GET or None)
            report_data = None
            
            if form.is_valid():
                # Check permission
                if not ReportPermission.can_view_agent_reports(request.user):
                    raise PermissionDenied("You don't have permission to view agent performance reports")
                
                # Get form data
                date_from = form.cleaned_data['date_from']
                date_to = form.cleaned_data['date_to']
                agent_id = form.cleaned_data['agent_id']
                metrics = form.cleaned_data['metrics']
                comparison_period = form.cleaned_data['comparison_period']
                
                # Initialize service
                performance_service = AgentPerformanceService()
                
                # Generate report
                report_data = performance_service.generate_agent_performance_report(
                    date_from=date_from,
                    date_to=date_to,
                    agent_id=agent_id,
                    metrics=metrics,
                    comparison_period=comparison_period
                )
            
            # Get agent list for admin users
            agents = []
            if request.user.user_type == 'admin':
                agents = AgentHierarchy.objects.filter(
                    parent_agent=request.user,
                    is_active=True
                ).select_related('child_agent')
            
            context = self.get_report_context(
                title='Agent Performance Report',
                data={'report_data': report_data, 'agents': agents},
                filters={'form': form}
            )
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect('flights:reports_dashboard')
        except Exception as e:
            logger.error(f"Agent performance report error: {str(e)}", exc_info=True)
            messages.error(request, 'Error generating agent performance report.')
            return render(request, self.template_name, {
                'error': str(e),
                'title': 'Agent Performance Report'
            })


class TeamPerformanceView(BaseReportingView, View):
    """Team Performance Report - Team-level analytics"""
    
    template_name = 'flights/reports/team_performance.html'
    
    def get(self, request):
        try:
            # Check permission (super agents and admin only)
            if request.user.user_type not in ['super_agent', 'admin']:
                raise PermissionDenied("You don't have permission to view team performance reports")
            
            # Get date range
            date_from = request.GET.get('date_from', '')
            date_to = request.GET.get('date_to', '')
            date_from, date_to = self.get_date_range(date_from, date_to)
            
            # Get team data
            team_data = self.get_team_performance_data(request.user, date_from, date_to)
            
            # Get team comparison
            team_comparison = self.get_team_comparison(request.user, date_from, date_to)
            
            # Get team trends
            team_trends = self.get_team_trends(request.user, date_from, date_to)
            
            context = self.get_report_context(
                title='Team Performance Report',
                data={
                    'team_data': team_data,
                    'team_comparison': team_comparison,
                    'team_trends': team_trends,
                    'date_from': date_from,
                    'date_to': date_to,
                },
                filters={
                    'date_from': date_from,
                    'date_to': date_to,
                }
            )
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect('flights:reports_dashboard')
        except Exception as e:
            logger.error(f"Team performance report error: {str(e)}", exc_info=True)
            messages.error(request, 'Error generating team performance report.')
            return render(request, self.template_name, {
                'error': str(e),
                'title': 'Team Performance Report'
            })
    
    def get_team_performance_data(self, user, date_from, date_to):
        """Get team performance data"""
        # Get team members
        if user.user_type == 'admin':
            # Admin sees all agents
            team_members = AgentHierarchy.objects.filter(
                is_active=True
            ).select_related('child_agent').distinct('child_agent')
        else:
            # Super agent sees their team
            team_members = AgentHierarchy.objects.filter(
                parent_agent=user,
                is_active=True
            ).select_related('child_agent')
        
        team_performance = []
        for member in team_members:
            agent = member.child_agent
            
            # Get agent bookings
            bookings = Booking.objects.filter(
                agent=agent,
                created_at__date__range=[date_from, date_to]
            )
            
            # Calculate metrics
            total_bookings = bookings.count()
            confirmed_bookings = bookings.filter(status='confirmed').count()
            total_revenue = bookings.filter(status='confirmed').aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')
            
            # Get conversion rate
            searches = FlightSearch.objects.filter(
                user=agent,
                created_at__date__range=[date_from, date_to]
            ).count()
            
            conversion_rate = 0
            if searches > 0:
                conversion_rate = (confirmed_bookings / searches) * 100
            
            # Get commission earned
            commission = CommissionTransaction.objects.filter(
                agent=agent,
                transaction_date__date__range=[date_from, date_to],
                status='earned'
            ).aggregate(total=Sum('commission_amount'))['total'] or Decimal('0.00')
            
            team_performance.append({
                'agent': agent,
                'total_bookings': total_bookings,
                'confirmed_bookings': confirmed_bookings,
                'cancellation_rate': ((total_bookings - confirmed_bookings) / total_bookings * 100) if total_bookings > 0 else 0,
                'total_revenue': total_revenue,
                'average_booking_value': total_revenue / confirmed_bookings if confirmed_bookings > 0 else Decimal('0.00'),
                'conversion_rate': conversion_rate,
                'commission_earned': commission,
                'search_count': searches,
            })
        
        # Sort by revenue (descending)
        team_performance.sort(key=lambda x: x['total_revenue'], reverse=True)
        
        return team_performance
    
    def get_team_comparison(self, user, date_from, date_to):
        """Compare team performance with previous period"""
        # Current period
        current_data = self.get_team_performance_data(user, date_from, date_to)
        
        # Previous period (same length)
        period_days = (date_to - date_from).days
        prev_date_to = date_from - timedelta(days=1)
        prev_date_from = prev_date_to - timedelta(days=period_days)
        
        previous_data = self.get_team_performance_data(user, prev_date_from, prev_date_to)
        
        # Create comparison
        comparison = {}
        for current in current_data:
            agent_id = current['agent'].id
            previous = next((p for p in previous_data if p['agent'].id == agent_id), None)
            
            if previous:
                comparison[agent_id] = {
                    'agent': current['agent'],
                    'current_revenue': current['total_revenue'],
                    'previous_revenue': previous['total_revenue'],
                    'revenue_change': ((current['total_revenue'] - previous['total_revenue']) / previous['total_revenue'] * 100) if previous['total_revenue'] > 0 else 0,
                    'current_bookings': current['confirmed_bookings'],
                    'previous_bookings': previous['confirmed_bookings'],
                    'booking_change': ((current['confirmed_bookings'] - previous['confirmed_bookings']) / previous['confirmed_bookings'] * 100) if previous['confirmed_bookings'] > 0 else 0,
                }
        
        return comparison
    
    def get_team_trends(self, user, date_from, date_to):
        """Get team performance trends over time"""
        # Calculate time periods (monthly for long periods, weekly for short)
        days_diff = (date_to - date_from).days
        
        if days_diff <= 90:
            # Weekly trends
            periods = []
            current_date = date_from
            while current_date <= date_to:
                period_end = min(current_date + timedelta(days=6), date_to)
                periods.append((current_date, period_end))
                current_date = period_end + timedelta(days=1)
        else:
            # Monthly trends
            periods = []
            year = date_from.year
            month = date_from.month
            
            while date(year, month, 1) <= date_to:
                period_start = date(year, month, 1)
                last_day = calendar.monthrange(year, month)[1]
                period_end = min(date(year, month, last_day), date_to)
                periods.append((period_start, period_end))
                
                # Move to next month
                month += 1
                if month > 12:
                    month = 1
                    year += 1
        
        # Get trends for each period
        trends = []
        for period_start, period_end in periods:
            period_data = self.get_team_performance_data(user, period_start, period_end)
            
            # Aggregate team metrics
            total_revenue = sum(d['total_revenue'] for d in period_data)
            total_bookings = sum(d['confirmed_bookings'] for d in period_data)
            total_commission = sum(d['commission_earned'] for d in period_data)
            
            trends.append({
                'period': period_start.strftime('%Y-%m-%d'),
                'period_label': self.get_period_label(period_start, period_end),
                'total_revenue': total_revenue,
                'total_bookings': total_bookings,
                'total_commission': total_commission,
                'agent_count': len(period_data),
                'average_revenue_per_agent': total_revenue / len(period_data) if period_data else Decimal('0.00'),
            })
        
        return trends
    
    def get_period_label(self, start_date, end_date):
        """Get label for period"""
        if (end_date - start_date).days <= 7:
            return start_date.strftime('%b %d')
        else:
            return start_date.strftime('%b %Y')


# ==============================================
# OPERATIONAL REPORTING VIEWS
# ==============================================

class BookingAnalysisView(BaseReportingView, View):
    """Booking Analysis Report - Booking patterns and trends"""
    
    template_name = 'flights/reports/booking_analysis.html'
    
    def get(self, request):
        try:
            form = BookingAnalysisForm(request.GET or None)
            report_data = None
            
            if form.is_valid():
                # Get form data
                date_from = form.cleaned_data['date_from']
                date_to = form.cleaned_data['date_to']
                analysis_type = form.cleaned_data['analysis_type']
                segment_by = form.cleaned_data['segment_by']
                
                # Initialize service
                analysis_service = BookingAnalyticsService()
                
                # Generate report
                report_data = analysis_service.generate_booking_analysis(
                    date_from=date_from,
                    date_to=date_to,
                    analysis_type=analysis_type,
                    segment_by=segment_by,
                    user=request.user
                )
            
            context = self.get_report_context(
                title='Booking Analysis Report',
                data={'report_data': report_data},
                filters={'form': form}
            )
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Booking analysis report error: {str(e)}", exc_info=True)
            messages.error(request, 'Error generating booking analysis report.')
            return render(request, self.template_name, {
                'error': str(e),
                'title': 'Booking Analysis Report'
            })


class AirlinePerformanceView(BaseReportingView, View):
    """Airline Performance Report - Airline-specific analytics"""
    
    template_name = 'flights/reports/airline_performance.html'
    
    def get(self, request):
        try:
            form = AirlineReportForm(request.GET or None)
            report_data = None
            
            if form.is_valid():
                # Get form data
                date_from = form.cleaned_data['date_from']
                date_to = form.cleaned_data['date_to']
                airline = form.cleaned_data['airline']
                metrics = form.cleaned_data['metrics']
                
                # Initialize service
                airline_service = AirlineAnalysisService()
                
                # Generate report
                report_data = airline_service.generate_airline_performance_report(
                    date_from=date_from,
                    date_to=date_to,
                    airline_code=airline.code if airline else None,
                    metrics=metrics,
                    user=request.user
                )
            
            context = self.get_report_context(
                title='Airline Performance Report',
                data={'report_data': report_data},
                filters={'form': form}
            )
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Airline performance report error: {str(e)}", exc_info=True)
            messages.error(request, 'Error generating airline performance report.')
            return render(request, self.template_name, {
                'error': str(e),
                'title': 'Airline Performance Report'
            })


class RouteAnalysisView(BaseReportingView, View):
    """Route Analysis Report - Popular routes and profitability"""
    
    template_name = 'flights/reports/route_analysis.html'
    
    def get(self, request):
        try:
            # Get date range
            date_from = request.GET.get('date_from', '')
            date_to = request.GET.get('date_to', '')
            date_from, date_to = self.get_date_range(date_from, date_to)
            
            # Get top routes
            top_routes = self.get_top_routes(request.user, date_from, date_to, limit=20)
            
            # Get route profitability
            route_profitability = self.get_route_profitability(request.user, date_from, date_to)
            
            # Get route trends
            route_trends = self.get_route_trends(request.user, date_from, date_to)
            
            context = self.get_report_context(
                title='Route Analysis Report',
                data={
                    'top_routes': top_routes,
                    'route_profitability': route_profitability,
                    'route_trends': route_trends,
                    'date_from': date_from,
                    'date_to': date_to,
                },
                filters={
                    'date_from': date_from,
                    'date_to': date_to,
                }
            )
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Route analysis report error: {str(e)}", exc_info=True)
            messages.error(request, 'Error generating route analysis report.')
            return render(request, self.template_name, {
                'error': str(e),
                'title': 'Route Analysis Report'
            })
    
    def get_top_routes(self, user, date_from, date_to, limit=20):
        """Get top routes by booking count"""
        # Base queryset
        if user.user_type == 'admin':
            bookings = Booking.objects.filter(
                created_at__date__range=[date_from, date_to],
                status='confirmed'
            )
        else:
            bookings = Booking.objects.filter(
                agent=user,
                created_at__date__range=[date_from, date_to],
                status='confirmed'
            )
        
        # Get route data from itineraries
        top_routes = bookings.values(
            'itinerary__search__origin__iata_code',
            'itinerary__search__origin__city',
            'itinerary__search__destination__iata_code',
            'itinerary__search__destination__city',
        ).annotate(
            booking_count=Count('id'),
            total_revenue=Sum('total_amount'),
            average_fare=Avg('total_amount'),
            passenger_count=Sum(
                Case(
                    When(passengers__passenger_type='ADT', then=1),
                    When(passengers__passenger_type='CHD', then=1),
                    When(passengers__passenger_type='INF', then=1),
                    default=0,
                    output_field=IntegerField()
                )
            )
        ).order_by('-booking_count')[:limit]
        
        # Format results
        formatted_routes = []
        for route in top_routes:
            formatted_routes.append({
                'origin_code': route['itinerary__search__origin__iata_code'],
                'origin_city': route['itinerary__search__origin__city'],
                'destination_code': route['itinerary__search__destination__iata_code'],
                'destination_city': route['itinerary__search__destination__city'],
                'route': f"{route['itinerary__search__origin__iata_code']} → {route['itinerary__search__destination__iata_code']}",
                'booking_count': route['booking_count'],
                'total_revenue': route['total_revenue'] or Decimal('0.00'),
                'average_fare': route['average_fare'] or Decimal('0.00'),
                'passenger_count': route['passenger_count'] or 0,
            })
        
        return formatted_routes
    
    def get_route_profitability(self, user, date_from, date_to):
        """Calculate route profitability"""
        # Get bookings with commission data
        if user.user_type == 'admin':
            bookings = Booking.objects.filter(
                created_at__date__range=[date_from, date_to],
                status='confirmed'
            ).prefetch_related('commission_transactions')
        else:
            bookings = Booking.objects.filter(
                agent=user,
                created_at__date__range=[date_from, date_to],
                status='confirmed'
            ).prefetch_related('commission_transactions')
        
        # Calculate profitability per route
        route_profitability = {}
        
        for booking in bookings:
            route_key = f"{booking.itinerary.search.origin.iata_code}-{booking.itinerary.search.destination.iata_code}"
            
            if route_key not in route_profitability:
                route_profitability[route_key] = {
                    'route': f"{booking.itinerary.search.origin.iata_code} → {booking.itinerary.search.destination.iata_code}",
                    'origin': booking.itinerary.search.origin.city,
                    'destination': booking.itinerary.search.destination.city,
                    'total_revenue': Decimal('0.00'),
                    'total_cost': Decimal('0.00'),
                    'total_commission': Decimal('0.00'),
                    'booking_count': 0,
                }
            
            # Add revenue
            route_profitability[route_key]['total_revenue'] += booking.total_amount
            route_profitability[route_key]['booking_count'] += 1
            
            # Calculate commission (cost)
            commission = booking.commission_transactions.filter(
                status='earned'
            ).aggregate(total=Sum('commission_amount'))['total'] or Decimal('0.00')
            
            route_profitability[route_key]['total_commission'] += commission
        
        # Calculate profit margin
        for route in route_profitability.values():
            route['total_cost'] = route['total_commission']  # Simplified cost model
            route['total_profit'] = route['total_revenue'] - route['total_cost']
            route['profit_margin'] = (route['total_profit'] / route['total_revenue'] * 100) if route['total_revenue'] > 0 else Decimal('0.00')
            route['average_profit_per_booking'] = route['total_profit'] / route['booking_count'] if route['booking_count'] > 0 else Decimal('0.00')
        
        # Sort by profitability
        profitability_list = list(route_profitability.values())
        profitability_list.sort(key=lambda x: x['profit_margin'], reverse=True)
        
        return profitability_list[:10]  # Return top 10
    
    def get_route_trends(self, user, date_from, date_to):
        """Get route booking trends over time"""
        # Group by month
        if user.user_type == 'admin':
            bookings = Booking.objects.filter(
                created_at__date__range=[date_from, date_to],
                status='confirmed'
            )
        else:
            bookings = Booking.objects.filter(
                agent=user,
                created_at__date__range=[date_from, date_to],
                status='confirmed'
            )
        
        # Get monthly trends for top 5 routes
        top_routes = self.get_top_routes(user, date_from, date_to, limit=5)
        route_trends = {}
        
        for route in top_routes:
            route_key = route['route']
            
            # Get monthly bookings for this route
            monthly_bookings = bookings.filter(
                itinerary__search__origin__iata_code=route['origin_code'],
                itinerary__search__destination__iata_code=route['destination_code']
            ).annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                booking_count=Count('id'),
                total_revenue=Sum('total_amount')
            ).order_by('month')
            
            route_trends[route_key] = {
                'route': route['route'],
                'trends': list(monthly_bookings),
                'total_bookings': route['booking_count'],
                'total_revenue': route['total_revenue'],
            }
        
        return route_trends


# ==============================================
# CUSTOM REPORTING VIEWS
# ==============================================

class CustomReportBuilderView(BaseReportingView, View):
    """Custom Report Builder - Create custom reports"""
    
    template_name = 'flights/reports/custom_report_builder.html'
    
    def get(self, request):
        try:
            form = CustomReportForm()
            
            # Get saved reports
            saved_reports = self.get_saved_reports(request.user)
            
            context = self.get_report_context(
                title='Custom Report Builder',
                data={'saved_reports': saved_reports},
                filters={'form': form}
            )
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Custom report builder error: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading custom report builder.')
            return render(request, self.template_name, {
                'error': str(e),
                'title': 'Custom Report Builder'
            })
    
    def post(self, request):
        try:
            form = CustomReportForm(request.POST)
            
            if form.is_valid():
                # Get form data
                report_name = form.cleaned_data['report_name']
                date_from = form.cleaned_data['date_from']
                date_to = form.cleaned_data['date_to']
                data_fields = form.cleaned_data['data_fields']
                filters = form.cleaned_data['filters']
                grouping = form.cleaned_data['grouping']
                sorting = form.cleaned_data['sorting']
                
                # Initialize service
                custom_service = CustomReportService()
                
                # Generate custom report
                report_data = custom_service.generate_custom_report(
                    report_name=report_name,
                    date_from=date_from,
                    date_to=date_to,
                    data_fields=data_fields,
                    filters=filters,
                    grouping=grouping,
                    sorting=sorting,
                    user=request.user
                )
                
                # Save report if requested
                if form.cleaned_data['save_report']:
                    self.save_custom_report(request.user, form.cleaned_data, report_data)
                
                context = self.get_report_context(
                    title=f'Custom Report: {report_name}',
                    data={'report_data': report_data, 'report_name': report_name},
                    filters={'form': form}
                )
                
                return render(request, 'flights/reports/custom_report_result.html', context)
            else:
                messages.error(request, 'Please correct the errors below.')
                return render(request, self.template_name, {
                    'form': form,
                    'title': 'Custom Report Builder'
                })
                
        except Exception as e:
            logger.error(f"Custom report generation error: {str(e)}", exc_info=True)
            messages.error(request, 'Error generating custom report.')
            return render(request, self.template_name, {
                'form': form,
                'error': str(e),
                'title': 'Custom Report Builder'
            })
    
    def get_saved_reports(self, user):
        """Get user's saved custom reports"""
        # This would typically query a SavedReport model
        # For now, return empty list
        return []
    
    def save_custom_report(self, user, report_config, report_data):
        """Save custom report configuration"""
        # This would typically save to a SavedReport model
        # For now, just log
        logger.info(f"User {user.id} saved custom report: {report_config['report_name']}")


# ==============================================
# EXPORT AND DOWNLOAD VIEWS
# ==============================================

class ReportExportView(BaseReportingView, View):
    """Export reports to various formats"""
    
    def get(self, request, report_type):
        try:
            # Get export parameters
            format = request.GET.get('format', 'excel')
            date_from = request.GET.get('date_from', '')
            date_to = request.GET.get('date_to', '')
            filters = json.loads(request.GET.get('filters', '{}'))
            
            # Validate export permission
            if not ReportPermission.can_export_reports(request.user):
                raise PermissionDenied("You don't have permission to export reports")
            
            # Initialize export service
            export_service = ReportExportService()
            
            # Generate and export report
            if report_type == 'sales':
                response = export_service.export_sales_report(
                    user=request.user,
                    date_from=date_from,
                    date_to=date_to,
                    export_format=format,
                    filters=filters
                )
            elif report_type == 'revenue':
                response = export_service.export_revenue_report(
                    user=request.user,
                    date_from=date_from,
                    date_to=date_to,
                    export_format=format,
                    filters=filters
                )
            elif report_type == 'commission':
                response = export_service.export_commission_report(
                    user=request.user,
                    date_from=date_from,
                    date_to=date_to,
                    export_format=format,
                    filters=filters
                )
            elif report_type == 'agent_performance':
                response = export_service.export_agent_performance_report(
                    user=request.user,
                    date_from=date_from,
                    date_to=date_to,
                    export_format=format,
                    filters=filters
                )
            elif report_type == 'airline':
                response = export_service.export_airline_report(
                    user=request.user,
                    date_from=date_from,
                    date_to=date_to,
                    export_format=format,
                    filters=filters
                )
            elif report_type == 'booking_analysis':
                response = export_service.export_booking_analysis_report(
                    user=request.user,
                    date_from=date_from,
                    date_to=date_to,
                    export_format=format,
                    filters=filters
                )
            else:
                return HttpResponse('Invalid report type', status=400)
            
            return response
            
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect('flights:reports_dashboard')
        except Exception as e:
            logger.error(f"Report export error: {str(e)}", exc_info=True)
            messages.error(request, 'Error exporting report.')
            return redirect('flights:reports_dashboard')


class ReportDownloadView(BaseReportingView, View):
    """Download generated reports"""
    
    def get(self, request, report_id):
        try:
            # Get report from cache or database
            report_data = cache.get(f"report_{report_id}")
            
            if not report_data:
                # Try to get from database
                # This would typically query a GeneratedReport model
                return HttpResponse('Report not found or expired', status=404)
            
            # Check if user can access this report
            if not self.can_access_report(request.user, report_data):
                raise PermissionDenied("You don't have permission to access this report")
            
            # Create download response
            format = request.GET.get('format', 'pdf')
            
            if format == 'pdf':
                return self.generate_pdf_response(report_data)
            elif format == 'excel':
                return self.generate_excel_response(report_data)
            elif format == 'csv':
                return self.generate_csv_response(report_data)
            else:
                return HttpResponse('Invalid format', status=400)
                
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect('flights:reports_dashboard')
        except Exception as e:
            logger.error(f"Report download error: {str(e)}", exc_info=True)
            messages.error(request, 'Error downloading report.')
            return redirect('flights:reports_dashboard')
    
    def can_access_report(self, user, report_data):
        """Check if user can access the report"""
        # Check if report belongs to user or user is admin
        if user.user_type == 'admin':
            return True
        
        report_owner_id = report_data.get('user_id')
        return str(user.id) == str(report_owner_id)
    
    def generate_pdf_response(self, report_data):
        """Generate PDF response"""
        buffer = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Prepare content
        elements = []
        styles = getSampleStyleSheet()
        
        # Add title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center
        )
        elements.append(Paragraph(report_data.get('title', 'Report'), title_style))
        elements.append(Spacer(1, 20))
        
        # Add report data as table
        if 'table_data' in report_data:
            table_data = report_data['table_data']
            if table_data:
                # Create table
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(table)
        
        # Build PDF
        doc.build(elements)
        
        # Create response
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{report_data.get("title", "report")}.pdf"'
        
        return response
    
    def generate_excel_response(self, report_data):
        """Generate Excel response"""
        wb = Workbook()
        ws = wb.active
        ws.title = report_data.get('title', 'Report')[:31]  # Excel sheet name limit
        
        # Add title
        ws.append([report_data.get('title', 'Report')])
        ws.append([])  # Empty row
        
        # Add report data
        if 'table_data' in report_data:
            for row in report_data['table_data']:
                ws.append(row)
        
        # Save to buffer
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        # Create response
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{report_data.get("title", "report")}.xlsx"'
        
        return response
    
    def generate_csv_response(self, report_data):
        """Generate CSV response"""
        buffer = StringIO()
        writer = csv.writer(buffer)
        
        # Add report data
        if 'table_data' in report_data:
            for row in report_data['table_data']:
                writer.writerow(row)
        
        # Create response
        response = HttpResponse(buffer.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{report_data.get("title", "report")}.csv"'
        
        return response


# ==============================================
# CHART AND VISUALIZATION VIEWS
# ==============================================

class ReportChartView(BaseReportingView, View):
    """Generate charts for reports"""
    
    def get(self, request):
        try:
            chart_type = request.GET.get('type', 'revenue_trend')
            date_from = request.GET.get('date_from', '')
            date_to = request.GET.get('date_to', '')
            
            # Get date range
            date_from, date_to = self.get_date_range(date_from, date_to)
            
            # Initialize chart generator
            chart_generator = ChartGenerator()
            
            # Generate chart based on type
            if chart_type == 'revenue_trend':
                chart_data = self.get_revenue_trend_data(request.user, date_from, date_to)
                chart = chart_generator.generate_line_chart(
                    data=chart_data,
                    title='Revenue Trend',
                    x_label='Date',
                    y_label='Revenue (SAR)'
                )
            elif chart_type == 'booking_distribution':
                chart_data = self.get_booking_distribution_data(request.user, date_from, date_to)
                chart = chart_generator.generate_bar_chart(
                    data=chart_data,
                    title='Booking Distribution by Airline',
                    x_label='Airline',
                    y_label='Number of Bookings'
                )
            elif chart_type == 'commission_pie':
                chart_data = self.get_commission_distribution_data(request.user, date_from, date_to)
                chart = chart_generator.generate_pie_chart(
                    data=chart_data,
                    title='Commission Distribution'
                )
            elif chart_type == 'conversion_rate':
                chart_data = self.get_conversion_rate_data(request.user, date_from, date_to)
                chart = chart_generator.generate_line_chart(
                    data=chart_data,
                    title='Conversion Rate Trend',
                    x_label='Week',
                    y_label='Conversion Rate (%)'
                )
            else:
                return HttpResponse('Invalid chart type', status=400)
            
            # Return chart as image
            response = HttpResponse(content_type='image/png')
            chart.savefig(response, format='png', dpi=100, bbox_inches='tight')
            plt.close(chart)
            
            return response
            
        except Exception as e:
            logger.error(f"Chart generation error: {str(e)}", exc_info=True)
            # Return empty image on error
            return HttpResponse(status=500)
    
    def get_revenue_trend_data(self, user, date_from, date_to):
        """Get revenue trend data for chart"""
        # Group by week
        if user.user_type == 'admin':
            bookings = Booking.objects.filter(
                created_at__date__range=[date_from, date_to],
                status='confirmed'
            )
        else:
            bookings = Booking.objects.filter(
                agent=user,
                created_at__date__range=[date_from, date_to],
                status='confirmed'
            )
        
        weekly_revenue = bookings.annotate(
            week=TruncDate('created_at')
        ).values('week').annotate(
            revenue=Sum('total_amount')
        ).order_by('week')
        
        # Format for chart
        chart_data = {
            'dates': [item['week'].strftime('%Y-%m-%d') for item in weekly_revenue],
            'values': [float(item['revenue'] or 0) for item in weekly_revenue]
        }
        
        return chart_data
    
    def get_booking_distribution_data(self, user, date_from, date_to):
        """Get booking distribution by airline"""
        if user.user_type == 'admin':
            bookings = Booking.objects.filter(
                created_at__date__range=[date_from, date_to],
                status='confirmed'
            )
        else:
            bookings = Booking.objects.filter(
                agent=user,
                created_at__date__range=[date_from, date_to],
                status='confirmed'
            )
        
        # Get bookings by airline
        airline_distribution = bookings.values(
            'itinerary__segments__airline__code',
            'itinerary__segments__airline__name'
        ).annotate(
            booking_count=Count('id', distinct=True)
        ).order_by('-booking_count')[:10]
        
        # Format for chart
        chart_data = {
            'labels': [f"{item['itinerary__segments__airline__code']}" for item in airline_distribution],
            'values': [item['booking_count'] for item in airline_distribution]
        }
        
        return chart_data
    
    def get_commission_distribution_data(self, user, date_from, date_to):
        """Get commission distribution data"""
        if user.user_type == 'admin':
            commissions = CommissionTransaction.objects.filter(
                transaction_date__date__range=[date_from, date_to],
                status='earned'
            )
        else:
            commissions = CommissionTransaction.objects.filter(
                agent=user,
                transaction_date__date__range=[date_from, date_to],
                status='earned'
            )
        
        # Group by airline
        commission_distribution = commissions.values(
            'airline__code',
            'airline__name'
        ).annotate(
            total_commission=Sum('commission_amount')
        ).order_by('-total_commission')[:8]
        
        # Format for chart
        chart_data = {
            'labels': [item['airline__code'] for item in commission_distribution],
            'values': [float(item['total_commission'] or 0) for item in commission_distribution],
            'colors': plt.cm.Set3(np.arange(len(commission_distribution)))
        }
        
        return chart_data
    
    def get_conversion_rate_data(self, user, date_from, date_to):
        """Get conversion rate trend data"""
        # Calculate weekly conversion rates
        weeks = []
        conversion_rates = []
        
        current_date = date_from
        while current_date <= date_to:
            week_end = min(current_date + timedelta(days=6), date_to)
            
            # Get searches for the week
            searches = FlightSearch.objects.filter(
                user=user,
                created_at__date__range=[current_date, week_end]
            ).count()
            
            # Get bookings for the week
            bookings = Booking.objects.filter(
                agent=user,
                created_at__date__range=[current_date, week_end],
                status='confirmed'
            ).count()
            
            # Calculate conversion rate
            conversion_rate = (bookings / searches * 100) if searches > 0 else 0
            
            weeks.append(current_date.strftime('%Y-%m-%d'))
            conversion_rates.append(conversion_rate)
            
            current_date = week_end + timedelta(days=1)
        
        return {
            'dates': weeks,
            'values': conversion_rates
        }


# ==============================================
# REPORT SCHEDULING VIEWS
# ==============================================

class ReportSchedulerView(BaseReportingView, View):
    """Schedule automated reports"""
    
    template_name = 'flights/reports/report_scheduler.html'
    
    def get(self, request):
        try:
            # Check permission
            if not ReportPermission.can_schedule_reports(request.user):
                raise PermissionDenied("You don't have permission to schedule reports")
            
            # Get user's scheduled reports
            scheduled_reports = self.get_scheduled_reports(request.user)
            
            context = self.get_report_context(
                title='Report Scheduler',
                data={'scheduled_reports': scheduled_reports}
            )
            
            return render(request, self.template_name, context)
            
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect('flights:reports_dashboard')
        except Exception as e:
            logger.error(f"Report scheduler error: {str(e)}", exc_info=True)
            messages.error(request, 'Error loading report scheduler.')
            return render(request, self.template_name, {
                'error': str(e),
                'title': 'Report Scheduler'
            })
    
    def post(self, request):
        try:
            # Schedule new report
            report_type = request.POST.get('report_type')
            schedule_type = request.POST.get('schedule_type')
            recipients = request.POST.get('recipients', '').split(',')
            format = request.POST.get('format', 'pdf')
            
            # Validate
            if not all([report_type, schedule_type]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('flights:report_scheduler')
            
            # Create scheduled report
            scheduled_report = self.create_scheduled_report(
                user=request.user,
                report_type=report_type,
                schedule_type=schedule_type,
                recipients=recipients,
                format=format
            )
            
            messages.success(request, f'Report scheduled successfully. Next run: {scheduled_report["next_run"]}')
            return redirect('flights:report_scheduler')
            
        except Exception as e:
            logger.error(f"Report scheduling error: {str(e)}", exc_info=True)
            messages.error(request, 'Error scheduling report.')
            return redirect('flights:report_scheduler')
    
    def get_scheduled_reports(self, user):
        """Get user's scheduled reports"""
        # This would typically query a ScheduledReport model
        # For now, return mock data
        return [
            {
                'id': 1,
                'report_type': 'sales',
                'schedule_type': 'weekly',
                'recipients': ['user@example.com'],
                'format': 'pdf',
                'next_run': (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
                'last_run': (timezone.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
                'status': 'active',
            }
        ]
    
    def create_scheduled_report(self, user, report_type, schedule_type, recipients, format):
        """Create a new scheduled report"""
        # This would typically create a ScheduledReport object
        # For now, return mock data
        return {
            'id': 2,
            'report_type': report_type,
            'schedule_type': schedule_type,
            'recipients': recipients,
            'format': format,
            'next_run': (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'status': 'active',
        }


# ==============================================
# HELPER METHODS
# ==============================================

    def get_report_types(self, user):
        """Get available report types for user"""
        report_types = [
            ('sales', 'Sales Report'),
            ('revenue', 'Revenue Report'),
            ('commission', 'Commission Report'),
            ('booking_analysis', 'Booking Analysis'),
            ('route_analysis', 'Route Analysis'),
        ]
        
        if user.user_type in ['super_agent', 'admin']:
            report_types.extend([
                ('agent_performance', 'Agent Performance'),
                ('team_performance', 'Team Performance'),
            ])
        
        if user.user_type == 'admin':
            report_types.extend([
                ('airline_performance', 'Airline Performance'),
                ('custom', 'Custom Report'),
            ])
        
        return report_types


# ==============================================
# URL CONFIGURATION FOR REPORTING
# ==============================================

"""
Add this to your flights/urls.py:

from django.urls import path
from .reporting_views import *

urlpatterns = [
    # Dashboard
    path('reports/dashboard/', SalesDashboardView.as_view(), name='reports_dashboard'),
    
    # Sales Reports
    path('reports/sales/', SalesReportView.as_view(), name='sales_report'),
    path('reports/revenue/', RevenueReportView.as_view(), name='revenue_report'),
    path('reports/commission/', CommissionReportView.as_view(), name='commission_report'),
    
    # Performance Reports
    path('reports/agent-performance/', AgentPerformanceView.as_view(), name='agent_performance_report'),
    path('reports/team-performance/', TeamPerformanceView.as_view(), name='team_performance_report'),
    
    # Operational Reports
    path('reports/booking-analysis/', BookingAnalysisView.as_view(), name='booking_analysis_report'),
    path('reports/airline-performance/', AirlinePerformanceView.as_view(), name='airline_performance_report'),
    path('reports/route-analysis/', RouteAnalysisView.as_view(), name='route_analysis_report'),
    
    # Custom Reports
    path('reports/custom-builder/', CustomReportBuilderView.as_view(), name='custom_report_builder'),
    
    # Export and Downloads
    path('reports/export/<str:report_type>/', ReportExportView.as_view(), name='report_export'),
    path('reports/download/<str:report_id>/', ReportDownloadView.as_view(), name='report_download'),
    
    # Charts
    path('reports/chart/', ReportChartView.as_view(), name='report_chart'),
    
    # Scheduling
    path('reports/scheduler/', ReportSchedulerView.as_view(), name='report_scheduler'),
]
"""