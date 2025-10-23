# Stocky Tee Time Booking Automation

An automated golf tee time booking system for Stocky Golf Course that uses Selenium WebDriver to book preferred tee times exactly when they become available (9 days in advance).

## Overview

This Python application automates the process of booking golf tee times at Stocky Golf Course by:
- Logging into the e-s-p.com booking system
- Waiting until the optimal time to attempt booking
- Selecting a date 9 days in the future
- Attempting to book the preferred time slot (or nearby alternatives)
- Running automatically via GitHub Actions on scheduled days

## Features

- **Intelligent Time Selection**: Prioritizes your preferred time but falls back to nearby slots
- **Automated Scheduling**: Runs via GitHub Actions on specific days/times
- **Retry Logic**: Persistently attempts to find and book available slots
- **Headless Operation**: Runs without UI for CI/CD compatibility
- **Configurable Parameters**: Username, password, and time preferences via environment variables

## Project Structure

```
Stocky/
├── program.py              # Main booking automation script
├── time_functions.py       # Date/time helper functions
├── requirements.txt        # Python dependencies
├── .github/
│   └── workflows/
│       ├── run-app.yml        # Workflow for user 1
│       └── run-app-eddie.yml  # Workflow for user 2
└── README.md
```

## How It Works

### Workflow

1. **Login** ([program.py:22-76](program.py#L22-L76))
   - Navigates to e-s-p.com login page
   - Sets clubid cookie to identify Stocky Golf Course
   - Authenticates with provided credentials

2. **Navigation** ([program.py:78-92](program.py#L78-L92))
   - Selects "Make Booking" option
   - Waits for booking calendar to load

3. **Time Generation** ([time_functions.py:15-49](time_functions.py#L15-L49))
   - Creates a prioritized list of times
   - Starts with preferred time, then alternates +/- 8 minutes
   - Example: For 10:00 preferred → [10:00, 10:08, 09:52, 10:16, 09:44, ...]

4. **Wait & Book** ([program.py:193-198](program.py#L193-L198))
   - Waits until 5:00 PM (configurable start time)
   - Refreshes page until target date appears
   - Attempts to book first available time from prioritized list
   - Submits booking form when successful

### GitHub Actions Schedule

The workflows run on:
- **Days**: Thursdays and Fridays
- **Time**: 5:30 PM UTC (4:30 PM GMT in winter, 5:30 PM BST in summer)
- **Wait Until**: 5:58 PM UTC before executing the booking script
- **Booking Time**: 6:00 PM UTC (when new slots become available)

## Setup & Installation

### Local Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Stocky
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install ChromeDriver**
   - The script uses `webdriver-manager` to automatically download ChromeDriver
   - Alternatively, manually install Chrome and ChromeDriver

4. **Run the script**
   ```bash
   python program.py '{"username": "your_username", "password": "your_password", "time_to_book": "10:00", "min_time": "09:00", "max_time": "11:00"}'
   ```

### GitHub Actions Setup

1. **Configure Repository Secrets** (Settings → Secrets and variables → Actions)
   - `MAD_AL_PASSWORD`: Password for user 1
   - `EDDIE_PASSWORD`: Password for user 2

2. **Configure Repository Variables**
   - `MAD_AL_USER`: Username for user 1
   - `EDDIE_USER`: Username for user 2
   - `SATURDAY_TIME`: Preferred booking time (e.g., "10:00")
   - `SATURDAY_MIN_TIME`: Minimum acceptable time (e.g., "09:00")
   - `SATURDAY_MAX_TIME`: Maximum acceptable time (e.g., "11:00")

3. **Workflows automatically run on schedule** or can be triggered manually via the Actions tab

## Configuration

### Script Parameters (JSON format)

| Parameter | Description | Example |
|-----------|-------------|---------|
| `username` | Golf course account username | `"john.doe@email.com"` |
| `password` | Golf course account password | `"SecurePass123"` |
| `time_to_book` | Preferred tee time (HH:MM format) | `"10:00"` |
| `min_time` | Earliest acceptable time | `"09:00"` |
| `max_time` | Latest acceptable time | `"11:00"` |

### Environment Variables (in code)

| Constant | Location | Default | Description |
|----------|----------|---------|-------------|
| `TIMEOUT` | [program.py:17](program.py#L17) | 10 | WebDriver wait timeout (seconds) |
| `MAX_RETRIES` | [program.py:18](program.py#L18) | 20 | Max page refresh attempts |
| `start_time` | [program.py:27-30](program.py#L27-L30) | 17:00 | Time to begin booking attempt |

## Dependencies

Core dependencies:
- **selenium (4.27.1)**: Web automation framework
- **webdriver-manager (4.0.2)**: Automatic ChromeDriver management
- **python-dotenv (1.0.1)**: Environment variable management

See [requirements.txt](requirements.txt) for full dependency list.

## Logging

Logs are written to:
- **Console** (stdout)
- **File** (`app.log`)

Log levels:
- `INFO`: Normal operation (login, booking attempts, success)
- `WARNING`: Retries and failures
- `ERROR`: Critical failures

## Known Limitations

1. **Date Boundary Issues**: The 9-day calculation uses day-of-month only, which may cause issues at month boundaries
2. **Single Course**: Currently hardcoded for Stocky (clubid: 1574)
3. **Fixed Retry Count**: 800 retries for finding available times (no overall timeout)
4. **Chrome Version**: GitHub workflow has hardcoded ChromeDriver version (132.0.6834.110)

## Troubleshooting

### Common Issues

**"Failed to find or click the day element"**
- The target date isn't available yet
- Increase `MAX_RETRIES` or check the booking window

**"Time did not appear within retries"**
- No slots available in your time range
- Widen `min_time` and `max_time` range
- Try different days (less competition)

**ChromeDriver version mismatch**
- Update the hardcoded version in `.github/workflows/run-app.yml`
- Or switch to using webdriver-manager in the workflow

**GitHub Action fails**
- Check secrets and variables are correctly set
- Review workflow logs in Actions tab
- Verify schedule timezone (UTC) matches your needs

## Future Improvements

Potential enhancements:
- [ ] Dynamic ChromeDriver version management in GitHub Actions
- [ ] Configurable start time via environment variables
- [ ] Better date calculation handling month boundaries
- [ ] Overall booking timeout protection
- [ ] Support for multiple golf courses
- [ ] Email/SMS notifications on success/failure
- [ ] Unit tests for time generation logic
- [ ] Docker containerization

## License

This project is for personal use. Ensure compliance with the golf course's terms of service.

## Contributing

This is a personal automation project. If you fork it:
1. Update the clubid cookie for your golf course
2. Modify the login URL if using a different booking system
3. Adjust timing parameters for your booking window

## Disclaimer

This tool automates legitimate booking activities for authorized users only. Users are responsible for:
- Ensuring compliance with the booking system's terms of service
- Keeping credentials secure
- Not overloading the booking system
- Canceling unwanted bookings promptly

Use at your own risk.
