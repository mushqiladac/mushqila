"""
Custom widgets for B2B Travel Mushqila forms
"""

from django import forms
from django.utils.translation import gettext_lazy as _


class SaudiPhoneInput(forms.TextInput):
    """Custom widget for Saudi phone numbers"""
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control',
            'placeholder': '+9665XXXXXXXX',
            'pattern': r'^\+9665\d{8}$',
            'title': _('Phone number must be in format: +9665XXXXXXXX'),
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class DatePickerInput(forms.DateInput):
    """Date picker widget"""
    
    input_type = 'date'
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class DateTimePickerInput(forms.DateTimeInput):
    """DateTime picker widget"""
    
    input_type = 'datetime-local'
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class CurrencyInput(forms.NumberInput):
    """Currency input widget"""
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class PercentageInput(forms.NumberInput):
    """Percentage input widget"""
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'max': '100',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class FileInputWithPreview(forms.ClearableFileInput):
    """File input with preview"""
    
    template_name = 'widgets/file_input_with_preview.html'
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class SelectWithSearch(forms.Select):
    """Select widget with search functionality"""
    
    template_name = 'widgets/select_with_search.html'
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-select select-with-search',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)