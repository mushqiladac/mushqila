# flights/views/search_views.py
"""
Flight search views for B2B Travel Platform
Production Ready - Final Version
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.db.models import Count, Avg, Min, Max
from django.utils import timezone
from django.core.cache import cache
from django.core.paginator import Paginator
import json
import logging
from datetime import datetime, timedelta
import hashlib

from flights.forms import (
    OneWaySearchForm,
    RoundTripSearchForm,
    MultiCitySearchForm,
    FlexSearchForm,
    FareCalendarForm,
)
from flights.models import (
    FlightSearch,
    FlightItinerary,
    Airport,
    Airline,
    AvailabilityCache,
)
from flights.services import FlightSearchService
from flights.services.galileo_client import galileo_client

logger = logging.getLogger(__name__)


class FlightSearchView(LoginRequiredMixin, TemplateView):
    """Main flight search view with different trip types"""
    
    template_name = 'flights/search/search_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get trip type from URL or default to one_way
        trip_type = self.request.GET.get('trip_type', 'one_way')
        
        # Initialize appropriate form
        if trip_type == 'one_way':
            form_class = OneWaySearchForm
        elif trip_type == 'round_trip':
            form_class = RoundTripSearchForm
        elif trip_type == 'multi_city':
            form_class = MultiCitySearchForm
        elif trip_type == 'flexible':
            form_class = FlexSearchForm
        else:
            form_class = OneWaySearchForm
        
        form = form_class(user=self.request.user)
        
        # Get popular routes for quick selection
        popular_routes = self.get_popular_routes()
        
        # Get recent searches for current user
        recent_searches = FlightSearch.objects.filter(
            user=self.request.user
        ).order_by('-created_at')[:5]
        
        # Get user's preferred airports
        user_profile = getattr(self.request.user, 'profile', None)
        preferred_airports = []
        if user_profile and hasattr(user_profile, 'preferred_airports'):
            preferred_airports = user_profile.preferred_airports.all()
        
        context.update({
            'form': form,
            'trip_type': trip_type,
            'popular_routes': popular_routes,
            'recent_searches': recent_searches,
            'preferred_airports': preferred_airports,
            'airlines': Airline.objects.filter(is_active=True),
            'page_title': 'Flight Search | B2B Travel Portal',
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        trip_type = request.POST.get('trip_type', 'one_way')
        
        # Initialize appropriate form
        if trip_type == 'one_way':
            form_class = OneWaySearchForm
        elif trip_type == 'round_trip':
            form_class = RoundTripSearchForm
        elif trip_type == 'multi_city':
            form_class = MultiCitySearchForm
        elif trip_type == 'flexible':
            form_class = FlexSearchForm
        else:
            form_class = OneWaySearchForm
        
        form = form_class(request.POST, user=request.user)
        
        if form.is_valid():
            try:
                # Generate search hash for caching
                search_data = form.cleaned_data
                search_hash = self.generate_search_hash(search_data)
                
                # Check cache first
                cache_key = f'search_results:{search_hash}'
                cached_results = cache.get(cache_key)
                
                if cached_results:
                    # Store in session for results page
                    request.session['search_results'] = cached_results
                    request.session['search_params'] = search_data
                    request.session['search_hash'] = search_hash
                    
                    messages.success(request, 'Found cached results.')
                    return redirect('flights:search_results')
                
                # Call flight search service
                search_service = FlightSearchService()
                results = search_service.search_flights(
                    user=request.user,
                    search_data=search_data
                )
                
                # Cache results for 5 minutes
                cache.set(cache_key, results, 300)
                
                # Store in session for results page
                request.session['search_results'] = results
                request.session['search_params'] = search_data
                request.session['search_hash'] = search_hash
                
                messages.success(
                    request,
                    f'Found {results.get("count", 0)} flight options.'
                )
                
                return redirect('flights:search_results')
                
            except Exception as e:
                logger.error(f"Flight search failed: {str(e)}", exc_info=True)
                messages.error(
                    request,
                    f'Search failed: {str(e)}. Please try again or contact support.'
                )
        else:
            messages.error(request, 'Please correct the errors below.')
        
        # Return form with errors
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)
    
    def generate_search_hash(self, search_data):
        """Generate unique hash for search parameters"""
        import json
        import hashlib
        
        # Remove user-specific data for caching
        cache_data = search_data.copy()
        if 'user' in cache_data:
            del cache_data['user']
        
        hash_string = json.dumps(cache_data, sort_keys=True, default=str)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def get_popular_routes(self):
        """Get popular flight routes for quick selection"""
        cache_key = 'popular_routes'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        # Calculate popular routes from recent searches
        one_month_ago = timezone.now() - timedelta(days=30)
        
        popular = FlightSearch.objects.filter(
            created_at__gte=one_month_ago
        ).values(
            'origin', 'destination'
        ).annotate(
            search_count=Count('id'),
            avg_passengers=Avg('adults')
        ).order_by('-search_count')[:10]
        
        # Enrich with airport information
        routes = []
        for route in popular:
            try:
                origin = Airport.objects.get(pk=route['origin'])
                destination = Airport.objects.get(pk=route['destination'])
                
                routes.append({
                    'origin': origin,
                    'destination': destination,
                    'search_count': route['search_count'],
                    'avg_passengers': route['avg_passengers'],
                })
            except Airport.DoesNotExist:
                continue
        
        # Cache for 1 hour
        cache.set(cache_key, routes, 3600)
        return routes


class SearchResultsView(LoginRequiredMixin, TemplateView):
    """Display flight search results"""
    
    template_name = 'flights/search/search_results.html'
    results_per_page = 20
    
    def get(self, request, *args, **kwargs):
        # Check if we have search results in session
        search_results = request.session.get('search_results')
        search_params = request.session.get('search_params')
        search_hash = request.session.get('search_hash')
        
        if not search_results or not search_params:
            messages.warning(request, 'No search results found. Please start a new search.')
            return redirect('flights:search')
        
        # Get filter parameters
        filters = self.get_filters(request)
        
        # Apply filters to results
        filtered_results = self.apply_filters(search_results, filters)
        
        # Paginate results
        paginator = Paginator(filtered_results.get('itineraries', []), self.results_per_page)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Sort options
        sort_options = [
            {'value': 'price_asc', 'label': 'Price: Low to High'},
            {'value': 'price_desc', 'label': 'Price: High to Low'},
            {'value': 'duration_asc', 'label': 'Duration: Shortest'},
            {'value': 'duration_desc', 'label': 'Duration: Longest'},
            {'value': 'departure_asc', 'label': 'Departure: Earliest'},
            {'value': 'departure_desc', 'label': 'Departure: Latest'},
            {'value': 'stops_asc', 'label': 'Stops: Fewest'},
            {'value': 'airline_asc', 'label': 'Airline: A-Z'},
        ]
        
        # Get selected sort
        sort_by = request.GET.get('sort', 'price_asc')
        
        # Sort itineraries
        if page_obj:
            sorted_itineraries = self.sort_itineraries(page_obj.object_list, sort_by)
            page_obj.object_list = sorted_itineraries
        
        context = {
            'results': search_results,
            'filtered_results': filtered_results,
            'search_params': search_params,
            'search_hash': search_hash,
            'page_obj': page_obj,
            'filters': filters,
            'sort_options': sort_options,
            'sort_by': sort_by,
            'page_title': 'Flight Results | B2B Travel Portal',
            'total_results': len(filtered_results.get('itineraries', [])),
            'has_filters': any(filters.values()),
        }
        
        return render(request, self.template_name, context)
    
    def get_filters(self, request):
        """Extract filter parameters from request"""
        return {
            'airlines': request.GET.getlist('airline'),
            'stops': request.GET.get('stops'),
            'price_min': request.GET.get('price_min'),
            'price_max': request.GET.get('price_max'),
            'departure_time_start': request.GET.get('departure_time_start'),
            'departure_time_end': request.GET.get('departure_time_end'),
            'arrival_time_start': request.GET.get('arrival_time_start'),
            'arrival_time_end': request.GET.get('arrival_time_end'),
            'cabin_class': request.GET.get('cabin_class'),
            'refundable': request.GET.get('refundable'),
            'direct_only': request.GET.get('direct_only'),
        }
    
    def apply_filters(self, results, filters):
        """Apply filters to search results"""
        itineraries = results.get('itineraries', [])
        filtered = []
        
        for itinerary in itineraries:
            # Airline filter
            if filters['airlines']:
                itinerary_airlines = set(seg.get('airline') for seg in itinerary.get('segments', []))
                filter_airlines = set(filters['airlines'])
                if not itinerary_airlines.intersection(filter_airlines):
                    continue
            
            # Stops filter
            if filters['stops']:
                max_stops = int(filters['stops'])
                total_stops = itinerary.get('total_stops', 0)
                if total_stops > max_stops:
                    continue
            
            # Price filter
            price = float(itinerary.get('pricing', {}).get('total_fare', 0))
            if filters['price_min']:
                if price < float(filters['price_min']):
                    continue
            if filters['price_max']:
                if price > float(filters['price_max']):
                    continue
            
            # Departure time filter
            if filters['departure_time_start'] and itinerary.get('segments'):
                first_segment = itinerary['segments'][0]
                departure_time = datetime.fromisoformat(first_segment.get('departure').replace('Z', '+00:00'))
                filter_time = datetime.strptime(filters['departure_time_start'], '%H:%M').time()
                if departure_time.time() < filter_time:
                    continue
            
            if filters['departure_time_end'] and itinerary.get('segments'):
                first_segment = itinerary['segments'][0]
                departure_time = datetime.fromisoformat(first_segment.get('departure').replace('Z', '+00:00'))
                filter_time = datetime.strptime(filters['departure_time_end'], '%H:%M').time()
                if departure_time.time() > filter_time:
                    continue
            
            # Cabin class filter
            if filters['cabin_class'] and filters['cabin_class'] != 'all':
                if itinerary.get('cabin_class') != filters['cabin_class']:
                    continue
            
            # Refundable filter
            if filters['refundable'] == 'true':
                if not itinerary.get('is_refundable'):
                    continue
            
            # Direct flights only
            if filters['direct_only'] == 'true':
                if itinerary.get('total_stops', 0) > 0:
                    continue
            
            filtered.append(itinerary)
        
        results['itineraries'] = filtered
        results['count'] = len(filtered)
        return results
    
    def sort_itineraries(self, itineraries, sort_by):
        """Sort itineraries based on criteria"""
        if sort_by == 'price_asc':
            return sorted(itineraries, key=lambda x: float(x.get('pricing', {}).get('total_fare', 0)))
        elif sort_by == 'price_desc':
            return sorted(itineraries, key=lambda x: float(x.get('pricing', {}).get('total_fare', 0)), reverse=True)
        elif sort_by == 'duration_asc':
            return sorted(itineraries, key=lambda x: self.parse_duration(x.get('total_duration', 'PT0H0M')))
        elif sort_by == 'duration_desc':
            return sorted(itineraries, key=lambda x: self.parse_duration(x.get('total_duration', 'PT0H0M')), reverse=True)
        elif sort_by == 'departure_asc':
            return sorted(itineraries, key=lambda x: x.get('segments', [{}])[0].get('departure', ''))
        elif sort_by == 'departure_desc':
            return sorted(itineraries, key=lambda x: x.get('segments', [{}])[0].get('departure', ''), reverse=True)
        elif sort_by == 'stops_asc':
            return sorted(itineraries, key=lambda x: x.get('total_stops', 0))
        elif sort_by == 'airline_asc':
            return sorted(itineraries, key=lambda x: x.get('segments', [{}])[0].get('airline_name', ''))
        else:
            return itineraries
    
    def parse_duration(self, duration_str):
        """Parse ISO 8601 duration string to minutes"""
        import re
        
        # Parse PT1H30M format
        hours = 0
        minutes = 0
        
        hour_match = re.search(r'(\d+)H', duration_str)
        if hour_match:
            hours = int(hour_match.group(1))
        
        minute_match = re.search(r'(\d+)M', duration_str)
        if minute_match:
            minutes = int(minute_match.group(1))
        
        return hours * 60 + minutes


class FareCalendarView(LoginRequiredMixin, View):
    """Fare calendar view showing prices by date"""
    
    template_name = 'flights/search/fare_calendar.html'
    
    def get(self, request, *args, **kwargs):
        form = FareCalendarForm(request.GET)
        
        if form.is_valid():
            try:
                search_service = FlightSearchService()
                
                month = int(form.cleaned_data['month'])
                year = int(form.cleaned_data['year'])
                
                calendar_data = search_service.get_fare_calendar(
                    origin=form.cleaned_data['origin'].iata_code,
                    destination=form.cleaned_data['destination'].iata_code,
                    month=month,
                    year=year
                )
                
                context = {
                    'form': form,
                    'calendar_data': calendar_data,
                    'month': month,
                    'year': year,
                    'month_name': self.get_month_name(month),
                    'page_title': 'Fare Calendar | B2B Travel Portal',
                }
                
                return render(request, self.template_name, context)
                
            except Exception as e:
                logger.error(f"Fare calendar failed: {str(e)}", exc_info=True)
                messages.error(request, f'Could not load fare calendar: {str(e)}')
        else:
            # Default to current month
            today = timezone.now()
            initial_data = {
                'month': str(today.month),
                'year': str(today.year),
            }
            form = FareCalendarForm(initial=initial_data)
        
        context = {
            'form': form,
            'page_title': 'Fare Calendar | B2B Travel Portal',
        }
        
        return render(request, self.template_name, context)
    
    def get_month_name(self, month):
        """Get month name from number"""
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        return months[month - 1] if 1 <= month <= 12 else ''


class FlexibleSearchView(LoginRequiredMixin, View):
    """Flexible date search view"""
    
    template_name = 'flights/search/flexible_search.html'
    
    def get(self, request, *args, **kwargs):
        form = FlexSearchForm(user=request.user)
        
        context = {
            'form': form,
            'page_title': 'Flexible Search | B2B Travel Portal',
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        form = FlexSearchForm(request.POST, user=request.user)
        
        if form.is_valid():
            try:
                # Process flexible search
                search_service = FlightSearchService()
                
                # Get date range
                date_range = form.cleaned_data.get('departure_date_range')
                
                # For flexible search, we might search multiple dates
                # Here we'll search for the start date and show flexibility options
                search_data = form.cleaned_data.copy()
                search_data['departure_date'] = date_range['start'] if date_range else timezone.now().date()
                search_data['flexible_dates'] = True
                
                results = search_service.search_flights(
                    user=request.user,
                    search_data=search_data
                )
                
                # Store in session
                request.session['search_results'] = results
                request.session['search_params'] = form.cleaned_data
                
                messages.success(
                    request,
                    f'Found {results.get("count", 0)} flexible flight options.'
                )
                
                return redirect('flights:search_results')
                
            except Exception as e:
                logger.error(f"Flexible search failed: {str(e)}", exc_info=True)
                messages.error(request, f'Search failed: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
        
        context = {
            'form': form,
            'page_title': 'Flexible Search | B2B Travel Portal',
        }
        
        return render(request, self.template_name, context)


class MultiCitySearchView(LoginRequiredMixin, View):
    """Multi-city search view"""
    
    template_name = 'flights/search/multi_city.html'
    
    def get(self, request, *args, **kwargs):
        form = MultiCitySearchForm(user=request.user)
        
        context = {
            'form': form,
            'page_title': 'Multi-City Search | B2B Travel Portal',
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        form = MultiCitySearchForm(request.POST, user=request.user)
        
        if form.is_valid():
            try:
                search_service = FlightSearchService()
                
                # Convert multi-city data to search format
                search_data = form.cleaned_data
                
                results = search_service.search_flights(
                    user=request.user,
                    search_data=search_data
                )
                
                # Store in session
                request.session['search_results'] = results
                request.session['search_params'] = form.cleaned_data
                
                messages.success(
                    request,
                    f'Found {results.get("count", 0)} multi-city flight options.'
                )
                
                return redirect('flights:search_results')
                
            except Exception as e:
                logger.error(f"Multi-city search failed: {str(e)}", exc_info=True)
                messages.error(request, f'Search failed: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
        
        context = {
            'form': form,
            'page_title': 'Multi-City Search | B2B Travel Portal',
        }
        
        return render(request, self.template_name, context)


@method_decorator(csrf_exempt, name='dispatch')
class AutoCompleteView(View):
    """Airport autocomplete API endpoint"""
    
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse({'results': []})
        
        # Search airports
        airports = Airport.objects.filter(
            is_active=True
        ).filter(
            models.Q(iata_code__icontains=query.upper()) |
            models.Q(city__icontains=query) |
            models.Q(name__icontains=query) |
            models.Q(country__icontains=query)
        )[:20]
        
        results = []
        for airport in airports:
            results.append({
                'id': airport.iata_code,
                'text': f"{airport.iata_code} - {airport.name}, {airport.city}, {airport.country}",
                'code': airport.iata_code,
                'city': airport.city,
                'country': airport.country,
                'name': airport.name,
            })
        
        return JsonResponse({'results': results})


class RecentSearchesView(LoginRequiredMixin, ListView):
    """View recent flight searches"""
    
    template_name = 'flights/search/recent_searches.html'
    context_object_name = 'searches'
    paginate_by = 20
    
    def get_queryset(self):
        return FlightSearch.objects.filter(
            user=self.request.user
        ).select_related(
            'origin', 'destination'
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Recent Searches | B2B Travel Portal'
        return context


class PopularRoutesView(LoginRequiredMixin, TemplateView):
    """View popular flight routes"""
    
    template_name = 'flights/search/popular_routes.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get popular routes from cache or calculate
        cache_key = 'popular_routes_detailed'
        popular_routes = cache.get(cache_key)
        
        if not popular_routes:
            one_month_ago = timezone.now() - timedelta(days=30)
            
            # Get routes with most searches
            routes = FlightSearch.objects.filter(
                created_at__gte=one_month_ago
            ).values(
                'origin', 'destination'
            ).annotate(
                search_count=Count('id'),
                avg_adults=Avg('adults'),
                avg_children=Avg('children'),
                latest_search=Max('created_at')
            ).order_by('-search_count')[:20]
            
            # Enrich with airport data and fare information
            popular_routes = []
            for route in routes:
                try:
                    origin = Airport.objects.get(pk=route['origin'])
                    destination = Airport.objects.get(pk=route['destination'])
                    
                    # Get average fare for this route
                    # This would typically come from a fare cache or historical data
                    
                    popular_routes.append({
                        'origin': origin,
                        'destination': destination,
                        'search_count': route['search_count'],
                        'avg_adults': route['avg_adults'],
                        'avg_children': route['avg_children'],
                        'latest_search': route['latest_search'],
                    })
                except Airport.DoesNotExist:
                    continue
            
            # Cache for 1 hour
            cache.set(cache_key, popular_routes, 3600)
        
        context.update({
            'popular_routes': popular_routes,
            'page_title': 'Popular Routes | B2B Travel Portal',
        })
        
        return context