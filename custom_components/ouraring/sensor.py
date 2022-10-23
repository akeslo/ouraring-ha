"""Platform for sensor integration."""
from __future__ import annotations

from datetime import datetime, timedelta
from dateutil import parser
import voluptuous as vol
import logging
from homeassistant.const import CONF_API_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import oura_api

TOKEN = ""
OURA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_TOKEN): str,
    }
)


def _seconds_to_hours(time_in_seconds):
    """Parses times in seconds and converts it to hours."""
    return round(int(time_in_seconds) / (60 * 60), 2)


def _datetime_to_time(received_date):
    return received_date


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    add_entities([OuraSleep(config, hass)])


class OuraSleep(Entity):

    """Representation of a Sensor."""

    def __init__(self, config, hass):
        """Initialize the sensor."""
        self._state = 0
        self._attributes = {}
        self._oura_token = config.get(CONF_API_TOKEN)

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Oura Ring Sleep"

    @property
    def state(self) -> int:
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self) -> str:
        """Return the state of the sensor."""
        return "mdi:sleep"

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return ""

    @property
    # pylint: disable=hass-return-type
    def extra_state_attributes(self):
        return self._attributes

    def update(self) -> None:
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        api = oura_api.OuraAPI()
        # now = datetime.now()
        # now_string = now.strftime("%Y-%m-%d")
        # yest = now - timedelta(1)
        # yest_string = yest.strftime("%Y-%m-%d")
        # tom = now + timedelta(1)
        # tom_string = tom.strftime("%Y-%m-%d")

        daily_sleep_response = api.get_data(
            self._oura_token, oura_api.OuraURLs.DAILY_SLEEP
        )

        if "data" in daily_sleep_response:
            self._state = daily_sleep_response["data"][0]["score"]
            logging.info("OuraRing: Score Updated: %s", self._state)

            sleep_response = api.get_data(self._oura_token, oura_api.OuraURLs.SLEEP)[
                "data"
            ]

            for item in sleep_response:
                if item["type"] == "long_sleep":
                    logging.info("OuraRing: Updating Sleep Data: %s", item)
                    bedtime_start = parser.parse(item["bedtime_start"])
                    bedtime_end = parser.parse(item["bedtime_end"])

                    self._attributes["data"] = {
                        "date": item["day"],
                        "bedtime_start_hour": bedtime_start.strftime("%H:%M"),
                        "bedtime_end_hour": bedtime_end.strftime("%H:%M"),
                        "breath_average": item["average_breath"],
                        "temperature_delta": item["readiness"]["temperature_deviation"],
                        "lowest_heart_rate": item["lowest_heart_rate"],
                        "heart_rate_average": item["average_heart_rate"],
                        "deep_sleep_duration": _seconds_to_hours(
                            item["deep_sleep_duration"]
                        ),
                        "rem_sleep_duration": _seconds_to_hours(
                            item["rem_sleep_duration"]
                        ),
                        "light_sleep_duration": _seconds_to_hours(
                            item["light_sleep_duration"]
                        ),
                        "total_sleep_duration": _seconds_to_hours(
                            item["total_sleep_duration"]
                        ),
                        "awake_duration": _seconds_to_hours(item["awake_time"]),
                        "in_bed_duration": _seconds_to_hours(item["time_in_bed"]),
                    }