from datetime import datetime, timedelta, time
from sortedcontainers import SortedList

class GenerateTimes:


    def __init__(self, preferred_time):

        # Get today's date
        today = datetime.today()

        # Add 9 days to today's date
        nine_days_from_today = today + timedelta(days=9)

        # Starting time
        self.start_time = datetime.strptime(f'{nine_days_from_today.year}-{nine_days_from_today.month}'
                                       f'-{nine_days_from_today.day}-05:28', '%Y-%m-%d-%H:%M')

        # End time
        self.end_time = datetime.strptime(f'{nine_days_from_today.year}-{nine_days_from_today.month}'
                                     f'-{nine_days_from_today.day}-21:30', '%Y-%m-%d-%H:%M')

        # Time interval
        self.interval = timedelta(minutes=8)

        # Initialize current time
        self.current_time = self.start_time

        self.min_time = datetime.strptime(f'{nine_days_from_today.year}-{nine_days_from_today.month}'
                                     f'-{nine_days_from_today.day}-08:00', '%Y-%m-%d-%H:%M')
        self.max_time = datetime.strptime(f'{nine_days_from_today.year}-{nine_days_from_today.month}'
                                     f'-{nine_days_from_today.day}-10:00', '%Y-%m-%d-%H:%M')
        self.preferred_time = datetime.strptime(f'{nine_days_from_today.year}-{nine_days_from_today.month}'
                                     f'-{nine_days_from_today.day}-{preferred_time}', '%Y-%m-%d-%H:%M')





    # Loop to generate and the times at 8-minute intervals
    def get_list_of_times(self) -> SortedList:

        sorted_list = SortedList()

        while ((self.current_time <= self.end_time ) and (self.current_time >= self.start_time )):

            if self.min_time.time() <= self.current_time.time() <= self.max_time.time():

                sorted_list.add(self.current_time)
                # print(current_time.strftime('%H:%M'))

            self.current_time += self.interval

        return sorted_list, self.min_time, self.max_time, self.preferred_time