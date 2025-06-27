from django.utils.dateparse import parse_date as django_parse_date
from datetime import datetime

def parse_date(date_str):
    """Safely parse a date string into a date object"""
    if not date_str:
        return None
    return django_parse_date(date_str)

def safe_isoformat(val):
    """Safely convert a date to ISO format string"""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.isoformat()
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return str(val) 