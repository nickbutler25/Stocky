import time as t
from datetime import datetime, timedelta
import logging
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from collections import namedtuple
from selenium.webdriver.support.wait import WebDriverWait

from time_functions import generate_times, day_nine_days_from_now, day_eight_days_from_now, get_uk_now
import sys
import json
import os
import pytz

# Load configuration from appsettings.json
def load_config():
    """
    Load configuration from appsettings.json file.

    Supports local overrides via appsettings.local.json which takes precedence.
    This allows developers to customize settings without modifying the base config.
    """
    script_dir = os.path.dirname(__file__) if __file__ else '.'
    base_config_path = os.path.join(script_dir, 'appsettings.json')
    local_config_path = os.path.join(script_dir, 'appsettings.local.json')

    config = {}

    # Load base configuration
    try:
        with open(base_config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        pass  # Will use defaults

    # Load local overrides if they exist
    try:
        with open(local_config_path, 'r') as f:
            local_config = json.load(f)
            config.update(local_config)  # Local settings override base settings
    except FileNotFoundError:
        pass  # Local config is optional

    return config

config = load_config()

# Configuration constants - loaded from appsettings.json with fallback defaults
TIMEOUT = config.get('WebDriverTimeout', 10)  # Timeout for WebDriverWait in seconds
MAX_RETRIES = config.get('MaxPageRetries', 20)  # Maximum number of retries for finding the day element
CLUB_ID = config.get('ClubId', '1574')  # Golf course club ID for e-s-p.com system
BOOKING_START_HOUR = config.get('BookingStartHour', 18)  # Hour to start attempting booking (24-hour format)
BOOKING_START_MINUTE = config.get('BookingStartMinute', 0)  # Minute to start attempting booking



def login_and_setup(username: str, password: str, time_to_book: str, min_time: str, max_time : str):
    # Get current UK time (handles BST/GMT automatically)
    uk_tz = pytz.timezone('Europe/London')
    uk_now = get_uk_now()
    today_uk = uk_now.date()

    from datetime import time
    # Set the booking start time from configuration
    booking_time = time(BOOKING_START_HOUR, BOOKING_START_MINUTE, 0)

    # Combine today's UK date with the booking time to create a timezone-aware datetime
    start_time_naive = datetime.combine(today_uk, booking_time)
    start_time = uk_tz.localize(start_time_naive)

    day_to_search = day_nine_days_from_now()
    day_before_search = day_eight_days_from_now()

    time_list = generate_times(time_to_book, min_time, max_time)

    logging.info(f'Booking a time between {min_time} and {max_time}')
    logging.info(f'Ideally at {time_to_book}')
    logging.info(f'On the following day {day_to_search}')

    # Use chromedriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # website details
        # login_url = "https://e-s-p.com//elitelive/selectsite.php"
        login_url = "https://e-s-p.com/elitelive/login.php"

        logging.info(f'Attempting to Login as {username}')
        # Open the Stockwood Vale Login page
        driver.get(login_url)

        # Add cookie so it opens on Stockwood Vale's page
        # Same software is used for multiple courses
        cookieClubId = {
            'name': 'clubid',
            'value': CLUB_ID,
            'domain': '.e-s-p.com'  # Make sure this matches the domain you are working with
        }
        driver.add_cookie(cookieClubId)
        driver.refresh()

        # ensure the login form has loaded
        sumbitLoginButton = WebDriverWait(driver, 40).until(
            EC.element_to_be_clickable((By.ID, "submit_login"))
        )

        # Input username and password and submit
        driver.find_element(By.ID, "username_field").send_keys(username)
        driver.find_element(By.ID, "password_field").send_keys(password)
        sumbitLoginButton.click()

        logging.info(f'Logged in Successfully')

        logging.info(f'Selecting Make Booking')
        # Select make booking
        makeBookingButton = WebDriverWait(driver, 40).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#fdbox_makebooking .ah_segment_frm_btn"))
        )
        makeBookingButton.click()
        driver.find_element(By.NAME, "Submit").click()
        logging.info(f'Make booking selected')

        logging.info(f'Waiting for dates to load')
        # Wait for calendar to load by checking for the previous day
        # This properly handles month boundaries (e.g., Oct 31 before Nov 1)
        WebDriverWait(driver, 40).until(
            EC.element_to_be_clickable((By.LINK_TEXT, str(day_before_search)))
        )
        logging.info(f'Dates loaded')
        wait_and_book(driver, start_time, day_to_search, day_before_search, time_list)
    finally:
        # Always close the browser, even if an error occurs
        logging.info('Closing browser')
        driver.quit()


def validate_inputs(start_time: datetime, day_to_search: int, day_before_search: int, time_list: list) -> None:
    """Validate the inputs to ensure they are in the correct format."""
    if not isinstance(start_time, datetime):
        raise ValueError("start_time must be a datetime object")

    if not isinstance(day_to_search, int) or day_to_search < 1 or day_to_search > 31:
        raise ValueError("day_to_search must be an integer between 1 and 31")

    if not isinstance(day_before_search, int) or day_before_search < 1 or day_before_search > 31:
        raise ValueError("day_before_search must be an integer between 1 and 31")

    if not isinstance(time_list, list) or not all(isinstance(item, str) for item in time_list):
        raise ValueError("time_list must be a list of strings")


def wait_until_start_time(start_time: datetime) -> None:
    """
    Wait until the specified start time is reached in UK timezone.

    Args:
        start_time: Timezone-aware datetime in UK timezone
    """
    logging.info(f'Waiting for start time of {start_time.strftime("%Y-%m-%d %H:%M:%S %Z")}')

    current_uk_time = get_uk_now()
    logging.info(f'Current UK time: {current_uk_time.strftime("%Y-%m-%d %H:%M:%S %Z")}')

    #while get_uk_now() < start_time:
    #    t.sleep(0.5)


def find_and_click_day_element(driver: webdriver, day_to_search: int, day_before_search: int) -> None:
    """Find and click the day element after refreshing the page until it appears."""
    retry = 0
    while retry < MAX_RETRIES:

        driver.refresh()
        logging.info(f'Refreshing page (Attempt {retry + 1} of {MAX_RETRIES})')

        # Wait for the previous day's element to ensure the page is loaded
        # This properly handles month boundaries (e.g., Oct 31 before Nov 1)
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.LINK_TEXT, str(day_before_search)))
        )

        logging.info(f'Clicking {day_to_search} as the date')
        elements = driver.find_elements(By.LINK_TEXT, str(day_to_search))
        if not elements:
            logging.warning(f"Attempt {retry} failed")
            retry += 1
        else:
            elements[0].click()
            return  # Exit the function if the element is found and clicked

    raise Exception(f"Failed to find or click the day element after {MAX_RETRIES} retries")


def book_preferred_time(driver: webdriver, time_list: [str]) -> None:
    """Book the preferred tee time."""
    try:
        retry = 0
        max_retry = 800
        while retry < max_retry:
            available_time  = get_available_time(driver, time_list)
            if not available_time:
                #logging.info(f"Attempt {retry + 1} failed")
                retry += 1
            else:
                element, time = available_time
                element.click()
                logging.info(f'Time Clicked: {time}')
                logging.info(f'Retry Count: {retry}')
                break

        if retry < max_retry:
            # Switch to the booking frame and submit the form
            driver.switch_to.frame(0)

            retry = 0
            while retry < 100:
                elements = driver.find_elements(By.NAME, "submit_frm_nopay")
                if not elements:
                    retry += 1
                else:
                    elements[0].click()
                    logging.info(f'Successfully booked the following time: {time}')

                    break

        else:
            logging.info(f'Time did not appear within {max_retry} retries, most likely time was not available')


    except Exception as e:
        logging.error(f"Failed to book the preferred time: {e}")
        raise


def get_available_time(driver: webdriver, time_list: str):

    for time_to_book in time_list:
        elements = driver.find_elements(By.LINK_TEXT, time_to_book)
        if elements:
            return elements[0], time_to_book

    return None



def wait_and_book(driver: webdriver, start_time: datetime, day_to_search: int, day_before_search: int, time_to_book: str) -> None:
    """Wait until the start time, find the day element, and book the preferred tee time."""
    validate_inputs(start_time, day_to_search, day_before_search, time_to_book)
    wait_until_start_time(start_time)
    find_and_click_day_element(driver, day_to_search, day_before_search)
    book_preferred_time(driver, time_to_book)


try:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),  # Log to a file
            logging.StreamHandler(sys.stdout)  # Log to the console
        ]
    )

    logging.info('Starting search for Stockwood Vale Tee Times')

    data = json.loads(sys.argv[1])
    username = data.get('username')
    password = data.get('password')
    time_to_book = data.get('time_to_book')
    min_time = data.get('min_time')
    max_time = data.get('max_time')

    login_and_setup(username, password, time_to_book, min_time, max_time)



except Exception as e:
    logging.error(e)
    raise
