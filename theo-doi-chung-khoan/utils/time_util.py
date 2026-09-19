"""
Timezone utility module for handling local time across the application.
Provides timezone-aware datetime functions for logging and notifications.
"""

import os
import time
from datetime import datetime, timedelta, timezone


def setup_local_timezone():
    """
    Set up the local timezone for the application.
    This ensures consistent timezone handling across the application.
    
    On Unix/Linux systems, sets the TZ environment variable and calls tzset().
    On Windows, this is a no-op as tzset() is not available.
    """
    # Try to get timezone from environment or use system default
    if not os.environ.get('TZ'):
        os.environ['TZ'] = 'Asia/Bangkok'
    
    try:
        time.tzset()
    except AttributeError:
        # tzset() not available on Windows
        pass


def get_local_now() -> datetime:
    """
    Get current local time as a timezone-aware datetime object.
    
    Returns:
        A timezone-aware datetime object in the local timezone.
        
    Example:
        >>> local_time = get_local_now()
        >>> print(local_time.strftime('%Y-%m-%d %H:%M:%S %z'))
        2026-09-19 14:01:41 +0700
    """
    return datetime.now(timezone.utc).astimezone()


def format_local_time(fmt: str = '%Y-%m-%d %H:%M:%S %z') -> str:
    """
    Format current local time as a string.
    
    Args:
        fmt: strftime format string. Default: '%Y-%m-%d %H:%M:%S %z'
        
    Returns:
        Formatted time string in local timezone.
        
    Example:
        >>> time_str = format_local_time()
        >>> print(time_str)
        2026-09-19 14:01:41 +0700
    """
    return get_local_now().strftime(fmt)


def format_local_time_for_log() -> str:
    """
    Format current local time for logging (with timezone abbreviation).
    
    Returns:
        Formatted time string: 'YYYY-MM-DD HH:MM:SS TZ+OFFSET'
        
    Example:
        >>> log_time = format_local_time_for_log()
        >>> print(log_time)
        2026-09-19 14:01:41 +0700
    """
    return format_local_time('%Y-%m-%d %H:%M:%S %z')


def format_local_time_for_message() -> str:
    """
    Format current local time for Telegram notifications.
    
    Returns:
        Formatted time string: 'DD/MM/YYYY HH:MM:SS'
        
    Example:
        >>> msg_time = format_local_time_for_message()
        >>> print(msg_time)
        19/09/2026 14:01:41
    """
    return format_local_time('%d/%m/%Y %H:%M:%S')


def get_next_schedule_time(interval_minutes: int) -> datetime:
    """
    Calculate the next scheduled time based on current time and interval.
    
    Args:
        interval_minutes: Interval in minutes until next schedule.
        
    Returns:
        A timezone-aware datetime object representing the next schedule.
        
    Example:
        >>> next_run = get_next_schedule_time(1)  # Next run in 1 minute
        >>> print(next_run.strftime('%Y-%m-%d %H:%M:%S %z'))
        2026-09-19 14:02:41 +0700
    """
    return get_local_now() + timedelta(minutes=interval_minutes)


def format_next_schedule(interval_minutes: int, fmt: str = '%Y-%m-%d %H:%M:%S %z') -> str:
    """
    Format the next scheduled time as a string.
    
    Args:
        interval_minutes: Interval in minutes until next schedule.
        fmt: strftime format string. Default: '%Y-%m-%d %H:%M:%S %z'
        
    Returns:
        Formatted next schedule time string.
        
    Example:
        >>> next_schedule = format_next_schedule(1)
        >>> print(next_schedule)
        2026-09-19 14:02:41 +0700
    """
    return get_next_schedule_time(interval_minutes).strftime(fmt)
