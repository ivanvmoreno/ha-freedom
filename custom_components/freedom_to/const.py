"""Constants for the Freedom.to integration."""

DOMAIN = "freedom_to"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

CONF_TEMPLATES = "session_templates"
CONF_DEFAULT_DURATION = "default_duration"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_NAME = "Freedom"
DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_SESSION_DURATION = 25  # minutes

# Service Names
SERVICE_START_SESSION = "start_session"
SERVICE_END_ALL_SESSIONS = "end_all_sessions"
SERVICE_END_SESSION = "end_session"
SERVICE_SET_LOCKED_MODE = "set_locked_mode"
SERVICE_ADD_SESSION_NOTE = "add_session_note"
