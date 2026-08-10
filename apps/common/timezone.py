"""
Timezone utilities for Event Planner project.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import zoneinfo


TIMEZONE_CHOICES = [(tz, tz) for tz in sorted(zoneinfo.available_timezones())]


def to_user_timezone(dt, user_tz):
    """
    Convert UTC datetime to user's timezone.
    """
    if dt is None:
        return None
    if not isinstance(user_tz, ZoneInfo):
        user_tz = ZoneInfo(user_tz)
    return dt.astimezone(user_tz)


def to_utc(dt, source_tz=None):
    """
    Convert datetime from source timezone to UTC.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        if source_tz is None:
            raise ValueError("source_tz required for naive datetime")
        if not isinstance(source_tz, ZoneInfo):
            source_tz = ZoneInfo(source_tz)
        dt = dt.replace(tzinfo=source_tz)
    return dt.astimezone(ZoneInfo('UTC'))


def is_valid_timezone(tz_name):
    """
    Check if timezone name is valid.
    """
    try:
        ZoneInfo(tz_name)
        return True
    except (KeyError, ValueError):
        return False


def get_current_time_in_timezone(tz_name):
    """
    Get current time in specified timezone.
    """
    tz = ZoneInfo(tz_name)
    return datetime.now(tz)


def format_datetime_for_display(dt, user_tz, format_str='%Y-%m-%d %H:%M:%S %Z'):
    """
    Format datetime for display in user's timezone.
    """
    if dt is None:
        return None
    local_dt = to_user_timezone(dt, user_tz)
    return local_dt.strftime(format_str)
