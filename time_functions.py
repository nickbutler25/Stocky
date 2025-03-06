from datetime import datetime, timedelta

def day_nine_days_from_now() -> int:
    # Get today's date
    today = datetime.today()

    # Calculate the date 9 days from now
    future_date = today + timedelta(days=9)

    # Format the day as 'dd'
    day_str = future_date.strftime('%d')

    return int(day_str)

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
