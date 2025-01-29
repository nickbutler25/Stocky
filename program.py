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
from times import GenerateTimes
import sys
import json

TIMEOUT = 20  # Timeout for WebDriverWait
MAX_RETRIES = 30  # Maximum number of retries for finding the day element
REFRESH_INTERVAL = 0.5  # Time interval between page refreshes (in seconds)


def login_and_setup(username, password, time_to_book):
    # Get today's date in UTC (GMT is the same as UTC)
    today = datetime.now().date()
    from datetime import time
    # Set the time to 6 PM (18:00)
    six_pm = time(18, 0)

    # Combine today's date with the 6 PM time to create a datetime object
    start_time = datetime.combine(today, six_pm)
    login_time = start_time - timedelta(minutes=1)

    # while datetime.now() < login_time:
    #    t.sleep(40)

    times = GenerateTimes(time_to_book)
    times_sorted_list, min_time, max_time, preferred_time = times.get_list_of_times()
    logging.info(f'Trying to book {preferred_time.time()}')

    day_to_search = times_sorted_list[0].day
    logging.info(f'On the following date {times_sorted_list[0].date()}')

    # Use chromedriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # website details
    # login_url = "https://e-s-p.com//elitelive/selectsite.php"
    login_url = "https://e-s-p.com/elitelive/login.php"

    logging.info(f'Attempting to Login as {username}')
    # Open the Stocky Login page
    driver.get(login_url)

    # Add cookie so it opens on Stocky's page
    # Same software is used for multiple courses
    cookieClubId = {
        'name': 'clubid',
        'value': '1574',
        'domain': '.e-s-p.com'  # Make sure this matches the domain you are working with
    }
    driver.add_cookie(cookieClubId)
    driver.refresh()

    # ensure the login form has loaded
    sumbitLoginButton = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "submit_auth"))
    )

    # Input username and password and submit
    driver.find_element(By.ID, "username_field").send_keys(username)
    driver.find_element(By.ID, "password_field").send_keys(password)
    sumbitLoginButton.click()

    logging.info(f'Logged in Successfully')

    logging.info(f'Selecting Make Booking')
    # Select make booking
    makeBookingButton = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#fdbox_makebooking .ah_segment_frm_btn"))
    )
    makeBookingButton.click()
    driver.find_element(By.NAME, "Submit").click()
    logging.info(f'Make booking selected')


    logging.info(f'Waiting for dates to load')
    # Select Date
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.LINK_TEXT, str(day_to_search - 1)))
    )
    logging.info(f'Dates loaded')
    wait_and_book(driver, start_time, day_to_search, time_to_book)


def validate_inputs(start_time: datetime, day_to_search: int, time_to_book: str) -> None:
    """Validate the inputs to ensure they are in the correct format."""
    if not isinstance(start_time, datetime):
        raise ValueError("start_time must be a datetime object")
    if not isinstance(day_to_search, int) or day_to_search < 1 or day_to_search > 31:
        raise ValueError("day_to_search must be an integer between 1 and 31")
    if not isinstance(time_to_book, str):
        raise ValueError("time_to_book must be a string")

def wait_until_start_time(start_time: datetime) -> None:
    """Wait until the specified start time is reached."""
    logging.info(f'Waiting for start time of {start_time}')
    logging.info(f'Time now of {datetime.now()}')
    #while datetime.now() < start_time:
    #    t.sleep(1)

def find_and_click_day_element(driver: webdriver, day_to_search: int) -> None:
    """Find and click the day element after refreshing the page until it appears."""
    retry = 0
    while retry < MAX_RETRIES:
        try:
            driver.refresh()
            logging.info(f'Refreshing page (Attempt {retry + 1} of {MAX_RETRIES})')

            # Wait for the previous day's element to ensure the page is loaded
            WebDriverWait(driver, TIMEOUT).until(
                EC.element_to_be_clickable((By.LINK_TEXT, str(day_to_search - 1)))
            )

            logging.info(f'Clicking {day_to_search} as the date')
            driver.find_element(By.LINK_TEXT, str(day_to_search)).click()
            return  # Exit the function if the element is found and clicked
        except Exception as e:
            logging.warning(f"Attempt {retry + 1} failed: {e}")
            retry += 1
            t.sleep(REFRESH_INTERVAL)

    raise Exception(f"Failed to find or click the day element after {MAX_RETRIES} retries")

def book_preferred_time(driver: webdriver, time_to_book: str) -> None:
    """Book the preferred tee time."""
    try:
        # Wait for the preferred time to be clickable
        time_to_book_element = WebDriverWait(driver, TIMEOUT).until(
            EC.element_to_be_clickable((By.LINK_TEXT, time_to_book))
        )
        logging.info(f'Booking time: {time_to_book}')
        time_to_book_element.click()

        # Switch to the booking frame and submit the form
        driver.switch_to.frame(0)
        driver.find_element(By.NAME, "submit_frm_nopay").click()
        logging.info(f'Successfully booked the following time: {time_to_book}')
    except Exception as e:
        logging.error(f"Failed to book the preferred time: {e}")
        raise

def wait_and_book(driver: webdriver, start_time: datetime, day_to_search: int, time_to_book: str) -> None:
    """Wait until the start time, find the day element, and book the preferred tee time."""
    validate_inputs(start_time, day_to_search, time_to_book)
    wait_until_start_time(start_time)
    find_and_click_day_element(driver, day_to_search)
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

    logging.info('Starting search for Stocky Tee Times')

    data = json.loads(sys.argv[1])
    username = data.get('username')
    password = data.get('password')
    time_to_book = data.get('time_to_book')

    login_and_setup(username, password, time_to_book)



except Exception as e:
    logging.error(e)
    raise








