"""Constants for integration_blueprint."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "cattainer_integration"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"
SIGNAL_CAT_DETECTED = "cattainer_cat_detected_signal"
