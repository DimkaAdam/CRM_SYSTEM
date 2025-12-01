"""
Utility functions for business logic calculations.
Business day logic: uses calendar dates without cutoff adjustments.
"""

from datetime import datetime, timedelta
from django.utils import timezone


def business_day(dt=None):
    """
    Returns the business day date.

    Business Logic:
    ---------------
    Each calendar day is its own business day.
    No cutoff time - records belong to the date they were created.

    Args:
        dt (datetime, optional): Datetime to calculate business day from.
                                If None, uses current time.

    Returns:
        date: The business day as a date object

    Examples:
        >>> from datetime import datetime
        >>> from django.utils import timezone

        >>> # Record at 11:30 PM on Jan 20
        >>> dt1 = timezone.make_aware(datetime(2025, 1, 20, 23, 30))
        >>> business_day(dt1)
        datetime.date(2025, 1, 20)

        >>> # Record at 12:01 AM on Jan 21
        >>> dt2 = timezone.make_aware(datetime(2025, 1, 21, 0, 1))
        >>> business_day(dt2)
        datetime.date(2025, 1, 21)
    """
    if dt is None:
        dt = timezone.now()

    # Get local timezone
    tz = timezone.get_current_timezone()

    # Convert to local time
    now_local = dt.astimezone(tz)

    # Return the calendar date
    return now_local.date()


def get_current_business_day():
    """
    Gets the current business day.

    Returns:
        date: Today's date as the business day

    Examples:
        >>> get_current_business_day()
        datetime.date(2025, 1, 21)
    """
    return business_day(timezone.now())


def format_business_day(dt=None):
    """
    Formats a datetime as a business day string in YYYY-MM-DD format.

    Args:
        dt (datetime, optional): Datetime to format. If None, uses current time.

    Returns:
        str: Business day in YYYY-MM-DD format

    Examples:
        >>> dt = timezone.make_aware(datetime(2025, 1, 20, 23, 30))
        >>> format_business_day(dt)
        '2025-01-20'
    """
    return business_day(dt).strftime('%Y-%m-%d')


def current_window(now=None):
    """
    Returns the current business day window (midnight to midnight).

    Business Logic:
    ---------------
    Window runs from 00:00:00 to 23:59:59 of the current calendar day.

    Args:
        now (datetime, optional): Reference time. If None, uses current time.

    Returns:
        tuple: (start_datetime, end_datetime) both timezone-aware

    Examples:
        >>> # At any time on Jan 21, 2025
        >>> start, end = current_window()
        >>> # start = 2025-01-21 00:00:00 (local TZ)
        >>> # end   = 2025-01-21 23:59:59 (local TZ)
    """
    tz = timezone.get_current_timezone()
    now_local = (now or timezone.now()).astimezone(tz)

    # Get current date
    d = now_local.date()

    # Window: midnight to just before next midnight
    start = timezone.make_aware(
        datetime(d.year, d.month, d.day, 0, 0, 0),
        timezone=tz
    )
    end = timezone.make_aware(
        datetime(d.year, d.month, d.day, 23, 59, 59),
        timezone=tz
    )

    return start, end


def previous_window(now=None):
    """
    Returns the previous business day window.

    Business Logic:
    ---------------
    Returns yesterday's window (yesterday 00:00:00 to 23:59:59).

    Args:
        now (datetime, optional): Reference time. If None, uses current time.

    Returns:
        tuple: (start_datetime, end_datetime) both timezone-aware

    Examples:
        >>> # On Jan 21, 2025
        >>> start, end = previous_window()
        >>> # start = 2025-01-20 00:00:00 (local TZ)
        >>> # end   = 2025-01-20 23:59:59 (local TZ)
    """
    tz = timezone.get_current_timezone()
    now_local = (now or timezone.now()).astimezone(tz)

    # Get yesterday's date
    yesterday = now_local.date() - timedelta(days=1)

    # Window: yesterday midnight to yesterday 23:59:59
    start = timezone.make_aware(
        datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0),
        timezone=tz
    )
    end = timezone.make_aware(
        datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59),
        timezone=tz
    )

    return start, end


def get_date_window(date_obj):
    """
    Returns the window (start, end) for a specific date.

    Args:
        date_obj (date): The date to get window for

    Returns:
        tuple: (start_datetime, end_datetime) both timezone-aware

    Examples:
        >>> from datetime import date
        >>> d = date(2025, 1, 20)
        >>> start, end = get_date_window(d)
        >>> # start = 2025-01-20 00:00:00 (local TZ)
        >>> # end   = 2025-01-20 23:59:59 (local TZ)
    """
    tz = timezone.get_current_timezone()

    start = timezone.make_aware(
        datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0),
        timezone=tz
    )
    end = timezone.make_aware(
        datetime(date_obj.year, date_obj.month, date_obj.day, 23, 59, 59),
        timezone=tz
    )

    return start, end


def is_same_business_day(dt1, dt2):
    """
    Checks if two datetimes fall on the same business day.

    Args:
        dt1 (datetime): First datetime
        dt2 (datetime): Second datetime

    Returns:
        bool: True if both are on the same business day

    Examples:
        >>> dt1 = timezone.make_aware(datetime(2025, 1, 20, 8, 0))
        >>> dt2 = timezone.make_aware(datetime(2025, 1, 20, 23, 0))
        >>> is_same_business_day(dt1, dt2)
        True

        >>> dt3 = timezone.make_aware(datetime(2025, 1, 21, 0, 1))
        >>> is_same_business_day(dt1, dt3)
        False
    """
    return business_day(dt1) == business_day(dt2)


def get_month_date_range(year, month):
    """
    Returns the date range for a given month.

    Args:
        year (int): Year (e.g., 2025)
        month (int): Month (1-12)

    Returns:
        tuple: (start_date, end_date) as date objects

    Examples:
        >>> start, end = get_month_date_range(2025, 1)
        >>> # start = 2025-01-01
        >>> # end   = 2025-01-31
    """
    from calendar import monthrange

    first_day = datetime(year, month, 1).date()
    last_day_num = monthrange(year, month)[1]
    last_day = datetime(year, month, last_day_num).date()

    return first_day, last_day


def get_month_window(year, month):
    """
    Returns the full datetime window for a given month.

    Args:
        year (int): Year (e.g., 2025)
        month (int): Month (1-12)

    Returns:
        tuple: (start_datetime, end_datetime) both timezone-aware

    Examples:
        >>> start, end = get_month_window(2025, 1)
        >>> # start = 2025-01-01 00:00:00 (local TZ)
        >>> # end   = 2025-01-31 23:59:59 (local TZ)
    """
    first_day, last_day = get_month_date_range(year, month)

    tz = timezone.get_current_timezone()

    start = timezone.make_aware(
        datetime.combine(first_day, datetime.min.time()),
        timezone=tz
    )
    end = timezone.make_aware(
        datetime.combine(last_day, datetime.max.time()),
        timezone=tz
    )

    return start, end