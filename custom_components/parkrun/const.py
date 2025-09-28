"""Constants for the Parkrun integration."""

DOMAIN = "parkrun"

# Default values
DEFAULT_NAME = "Parkrun"
DEFAULT_SCAN_INTERVAL = 60  # minutes

# URLs
PARKRUN_BASE_URL = "https://www.parkrun.org.uk"
PARKRUN_PROFILE_URL = "https://www.parkrun.org.uk/parkrunner/{user_id}/"

# Sensor attributes
ATTR_USER_ID = "user_id"
ATTR_TOTAL_RUNS = "total_runs"
ATTR_RECENT_RUNS = "recent_runs"
ATTR_LAST_RUN_DATE = "last_run_date"
ATTR_LAST_RUN_TIME = "last_run_time"
ATTR_LAST_RUN_POSITION = "last_run_position"
ATTR_LAST_RUN_EVENT = "last_run_event"
ATTR_PERSONAL_BEST = "personal_best"
ATTR_AVERAGE_TIME = "average_time"