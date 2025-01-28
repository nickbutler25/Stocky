import time as t
from datetime import datetime, time, timedelta
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
import asyncio
import sys


async def time_search(username, password, preferred_time):
    # Get today's date in UTC (GMT is the same as UTC)
    today = datetime.now().date()
    from datetime import time
    # Set the time to 6 PM (18:00)
    six_pm = time(13, 0)

    # Combine today's date with the 6 PM time to create a datetime object
    start_time = datetime.combine(today, six_pm)
    login_time = start_time - timedelta(minutes=1)

    # while datetime.now() < login_time:
    #    t.sleep(40)

    times = GenerateTimes(preferred_time)
    times_sorted_list, min_time, max_time, preferred_time = times.get_list_of_times()
    logging.info(f'Searching with a minimum time of {min_time.time()}')
    logging.info(f'a maximum time of {max_time.time()}')
    logging.info(f'trying to find a time closest to {preferred_time.time()} as possible')

    day_to_search = times_sorted_list[0].day
    logging.info(f'On the following date {times_sorted_list[0].date()}')

    # Setup Chrome options
    #chrome_options = Options()
    # Optional: run Chrome in headless mode

    # Setup the Chrome service
    #service = Service(r'C:\Chrome\chromedriver-win64\chromedriver.exe')
    #service.start()

    # Create the Remote WebDriver with options
    #driver = webdriver.Remote(
    #    command_executor=service.service_url,
    #    options=chrome_options
    #)

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

    logging.info(f'Waiting for start time of {start_time.time()} ')
    # IF TIME >= than start time refresh page wait for day -1 then check for day
    while datetime.now() < start_time:
        t.sleep(1)

    elements = None
    retry = 0
    while elements == None and retry < 10:
        driver.refresh()

        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.LINK_TEXT, str(day_to_search - 1)))
        )
        logging.info(f'Clicking {day_to_search} as the date')
        elements = driver.find_elements(By.LINK_TEXT, str(day_to_search))
        retry += 1

    elements[0].click()

    logging.info(f'Waiting for tee times to load')
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.LINK_TEXT, str('18:56')))  # ToDo come up with something better than this
    )
    logging.info(f'Times loaded')

    Item = namedtuple("teeTime", ["element", "time", "minutesFromIdeal"])
    time_list = []

    logging.info(f'Finding available times')
    # Find available times
    for tee_time in times_sorted_list:
        # Attempt to find the element by ID
        elements = driver.find_elements(By.LINK_TEXT, str(f"{tee_time.hour:02}") + ":" + str(f"{tee_time.minute:02}"))
        if elements:
            time_list.append(
                Item(element=elements[0], time=str(f"{tee_time.hour:02}") + ":" + str(f"{tee_time.minute:02}"),
                     minutesFromIdeal=abs(((tee_time - preferred_time).total_seconds()) / 60)))

    logging.info(f'Ranking Times')
    ranked_available_times = sorted(time_list, key=lambda x: x.minutesFromIdeal)

    logging.info('Booking Best Time')
    for time in ranked_available_times:
        try:
            time.element.click()  # Attempt to click on best time
            # bookButton = WebDriverWait(driver, 20).until(
            #    EC.element_to_be_clickable((By.NAME, "submit_frm_nopay"))
            # )
            # bookButton.click() #Click making booking
            driver.switch_to.frame(0)
            driver.find_element(By.NAME, "submit_frm_nopay").click()
            logging.info(f'Successfully Booked the following time {time.time}')
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")

    times = [item.time for item in ranked_available_times]
    logging.info(f'Times available between {min_time} and {max_time}')
    logging.info(times)
    t.sleep(5)


async def main():

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

        username = "alexhicks"
        password = "Spencer03"


        ##eusername = "ejmulcahy"
        ##epassword = "edge1982"


        tasks = [
            time_search(username, password, "09:04")
            ##time_search(username, password, "9:20"),
            ##time_search(username, password, "08:48"),
            ##time_search(eusername, epassword, "09:12"),
            ##time_search(eusername, epassword, "08:56"),
            ##time_search(eusername, epassword, "9:28")
        ]

        results = await asyncio.gather(*tasks)


    except Exception as e:
        logging.error(e)


asyncio.run(main())





