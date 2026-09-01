"""Constants for the ESB Lights integration.

Notes:
09/01/2026 - Created so the API address and key are entered in the HA UI at
             install time rather than hand-written into secrets.yaml
"""

DOMAIN = "esblights"

#Config entry keys
CONF_HOST = "host"
CONF_API_KEY = "api_key"
CONF_SCAN_INTERVAL = "scan_interval"

#The API changes at most once a day, so hourly is plenty
DEFAULT_SCAN_INTERVAL = 3600
MIN_SCAN_INTERVAL = 60

DEFAULT_PORT = 4000
API_PATH = "/api/esb-light-data"
HEALTH_PATH = "/healthz"

#Attributes carried on the sensor
ATTR_HEX_CODES = "hexCodes"
ATTR_XYZ_CODES = "xyzCodes"
ATTR_REASON = "reason"
