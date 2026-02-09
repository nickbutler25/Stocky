# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stockwood Vale Tee Time Booking Automation - a Python/Selenium script that automatically books golf tee times at Stockwood Vale Golf Course exactly when they become available (9 days in advance at 6:00 PM UK time).

**Critical Context**: This is a time-sensitive automation system. The booking window opens at 18:00 (6:00 PM) UK time, and slots fill up quickly. The system is designed to start attempting bookings at 17:58 PM to be ready immediately when the window opens.

## Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the booking script (replace with actual credentials)
python program.py '{"username": "user@email.com", "password": "pass", "time_to_book": "10:00", "min_time": "09:00", "max_time": "11:00"}'

# Test with local config overrides (create appsettings.local.json)
# appsettings.local.json is gitignored and won't be committed
```

### Testing & Debugging
- No formal test suite exists
- Use `appsettings.local.json` to override config values during development without modifying the base config
- Logs written to both `app.log` file and stdout
- Run locally with shorter wait times by modifying `BookingStartHour` in `appsettings.local.json`

### GitHub Actions
- Workflows run automatically via cron schedules on Thursdays and Fridays at 5:30 PM UK time
- Manual trigger available via GitHub Actions UI → "Run workflow" button
- Check logs in the Actions tab for debugging failed runs

## Architecture

### Timezone Handling (Critical)
**All times operate in UK timezone (Europe/London)** with automatic BST/GMT transition handling:
- `get_uk_now()` in `time_functions.py` is the single source of truth for current UK time
- GitHub Actions workflows use multiple cron schedules to account for BST (UTC+1) and GMT (UTC+0)
- The wait logic in workflows calculates UK time using `TZ='Europe/London'` environment variable
- Configuration values `BookingStartHour` and `BookingStartMinute` are interpreted in UK timezone
- Never use system local time or UTC without conversion

### Main Script Flow (`program.py`)
1. **Configuration Loading** (`load_config()`: 20-48)
   - Loads `appsettings.json` for base config
   - Optionally merges `appsettings.local.json` for developer overrides
   - All config has fallback defaults

2. **Login & Setup** (`login_and_setup()`: 61-149)
   - Calculates booking target date (9 days from now in UK timezone)
   - Generates prioritized time list using `generate_times()`
   - Initializes headless Chrome with webdriver-manager
   - Sets `clubid` cookie (1574 for Stockwood Vale) to identify the golf course
   - Logs into e-s-p.com booking system
   - Navigates to booking calendar

3. **Wait & Book** (`wait_and_book()`: 261-266)
   - `wait_until_start_time()`: Polls every 0.5s until `BookingStartHour:BookingStartMinute` UK time
   - `find_and_click_day_element()`: Refreshes page up to `MAX_RETRIES` times until target date appears
   - `book_preferred_time()`: Retries up to 800 times to find available slot from prioritized time list

4. **Time Selection Strategy** (`generate_times()` in `time_functions.py`: 55-89)
   - Creates prioritized list starting with preferred time
   - Alternates +/- 8 minute increments
   - Example: 10:00 → [10:00, 10:08, 09:52, 10:16, 09:44, 10:24, 09:36, ...]
   - Respects min_time and max_time boundaries

### Key Implementation Details

**Month Boundary Handling**:
- Uses `day_eight_days_from_now()` to verify calendar loaded before clicking target date
- Properly handles cases like Oct 23 → Nov 1 (waits for Oct 31 element first)

**Cookie-Based Golf Course Selection**:
- e-s-p.com serves multiple golf courses
- `clubid` cookie set to "1574" identifies Stockwood Vale
- Cookie must be set before authentication

**Retry Strategy**:
- Page refresh retries: `MAX_RETRIES` (default 20) for date element to appear
- Booking retries: Hard-coded 800 attempts to find available time slot
- No exponential backoff or overall timeout (intentional for competitive booking)

**WebDriver Configuration**:
- Always runs headless (`--headless` flag)
- Uses `webdriver-manager` for automatic ChromeDriver installation
- Requires Chrome browser installed (handled in GitHub Actions workflow)

## Configuration Files

### `appsettings.json`
- `WebDriverTimeout`: Selenium wait timeout in seconds (default: 10)
- `MaxPageRetries`: Max page refreshes when searching for dates (default: 20)
- `ClubId`: Golf course identifier for e-s-p.com (default: "1574")
- `BookingStartHour`: Hour to begin booking attempts in 24-hour format (default: 18)
- `BookingStartMinute`: Minute to begin booking attempts (default: 0)

### `appsettings.local.json` (optional, gitignored)
Developer override file that merges with base config. Useful for testing with different parameters without committing changes.

## GitHub Actions Workflow

### Environment Setup
- Ubuntu latest runner
- Python 3.13
- Google Chrome installed via .deb package
- tzdata package for timezone conversions

### Secrets & Variables
**Secrets** (Settings → Secrets and variables → Actions):
- `MAD_AL_PASSWORD`, `EDDIE_PASSWORD`: User passwords

**Variables**:
- `MAD_AL_USER`, `EDDIE_USER`: Usernames
- `SATURDAY_TIME`: Preferred booking time (e.g., "10:00")
- `SATURDAY_MIN_TIME`, `SATURDAY_MAX_TIME`: Acceptable time range

### Workflow Timing
- Triggers at 5:30 PM UK time via multiple cron schedules (handles BST/GMT)
- Waits until 5:58 PM UK time before executing script
- Script begins attempting bookings, ready for 6:00 PM slot release

## Common Pitfalls

1. **Timezone Confusion**: Never use `datetime.now()` without timezone awareness. Always use `get_uk_now()`.

2. **Hard-Coded Retry Counts**: The 800-retry booking loop in `book_preferred_time()` has no timeout. This is intentional for competitive booking but could hang indefinitely.

3. **Cookie Timing**: The `clubid` cookie must be set after initial page load but before login form submission.

4. **Month Boundaries**: When calculating dates 8-9 days in the future, don't assume same month. Use `timedelta` and extract `.day` property.

5. **JSON Argument Parsing**: Script expects JSON string as `sys.argv[1]`. In workflows, ensure proper escaping of quotes and no extra spaces in JSON.

6. **Submit Button Polling**: Uses 200ms poll frequency (`poll_frequency=0.2`) for faster detection when booking form loads.
