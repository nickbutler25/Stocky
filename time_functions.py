from datetime import datetime, timedelta

def day_nine_days_from_now() -> int:
    """
    Calculate the day number 9 days from now.

    Returns:
        int: The day of the month (1-31) for the date 9 days in the future.

    Note: This function properly handles month boundaries. For example:
        - Jan 25 + 9 days = Feb 3 (returns 3)
        - Dec 28 + 9 days = Jan 6 next year (returns 6)
    """
    # Get today's date
    today = datetime.today()

    # Calculate the date 9 days from now
    future_date = today + timedelta(days=9)

    # Return the day of the month (1-31)
    # The .day property automatically handles month boundaries correctly
    return future_date.day

def day_eight_days_from_now() -> int:
    """
    Calculate the day number 8 days from now (one day before the booking target).

    This is used to verify the calendar has loaded before attempting to click
    the target date. It properly handles month boundaries.

    Returns:
        int: The day of the month (1-31) for the date 8 days in the future.

    Examples:
        - If today is Oct 23 and target is Nov 1 (9 days):
          This returns Oct 31 (8 days) = 31
        - If today is Jan 24 and target is Feb 2 (9 days):
          This returns Feb 1 (8 days) = 1
    """
    today = datetime.today()
    future_date = today + timedelta(days=8)
    return future_date.day

def generate_times(preferred_time: str, min_time: str, max_time: str):
    def time_to_minutes(time_str: str) -> int:
        """Convert time string hh:mm to minutes since midnight."""
        h, m = map(int, time_str.split(':'))
        return h * 60 + m

    def minutes_to_time(minutes: int) -> str:
        """Convert minutes since midnight to time string hh:mm."""
        h = minutes // 60
        m = minutes % 60
        return f"{h:02d}:{m:02d}"

    preferred_minutes = time_to_minutes(preferred_time)
    max_minutes = time_to_minutes(max_time)
    min_minutes = time_to_minutes(min_time)

    times = [preferred_time]
    increment = 8
    i = 1

    while True:
        add_time = preferred_minutes + i * increment
        sub_time = preferred_minutes - i * increment

        if add_time <= max_minutes:
            times.append(minutes_to_time(add_time))
        if sub_time >= min_minutes:
            times.append(minutes_to_time(sub_time))

        if add_time > max_minutes and sub_time < min_minutes:
            break

        i += 1

    return times
