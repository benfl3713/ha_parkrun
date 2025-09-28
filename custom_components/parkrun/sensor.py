"""Parkrun sensor platform."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    ATTR_AVERAGE_TIME,
    ATTR_LAST_RUN_DATE,
    ATTR_LAST_RUN_EVENT,
    ATTR_LAST_RUN_POSITION,
    ATTR_LAST_RUN_TIME,
    ATTR_PERSONAL_BEST,
    ATTR_RECENT_RUNS,
    ATTR_TOTAL_RUNS,
    ATTR_USER_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PARKRUN_PROFILE_URL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Parkrun sensor."""
    user_id = config_entry.data["user_id"]
    name = config_entry.data.get("name", "Parkrun")
    
    coordinator = ParkrunDataUpdateCoordinator(hass, user_id)
    await coordinator.async_config_entry_first_refresh()
    
    async_add_entities([ParkrunSensor(coordinator, user_id, name)], True)


class ParkrunDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Parkrun data."""

    def __init__(self, hass: HomeAssistant, user_id: str) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL),
        )
        self.user_id = user_id
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            return await self._fetch_parkrun_data()
        except Exception as exception:
            raise UpdateFailed(f"Error communicating with API: {exception}") from exception

    async def _fetch_parkrun_data(self) -> dict[str, Any]:
        """Fetch data from Parkrun website."""
        url = PARKRUN_PROFILE_URL.format(user_id=self.user_id)
        
        try:
            async with self.session.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0 Chrome/140.0.0.0 Safari/537.36"}) as response:
                if response.status != 200:
                    raise UpdateFailed(f"HTTP {response.status} error fetching data")
                
                content = await response.text()
                return self._parse_parkrun_data(content)
                
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout fetching Parkrun data") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error fetching Parkrun data: {err}") from err

    def _parse_parkrun_data(self, html_content: str) -> dict[str, Any]:
        """Parse the HTML content from Parkrun profile page."""
        soup = BeautifulSoup(html_content, 'html.parser')
        data = {
            ATTR_USER_ID: self.user_id,
            ATTR_TOTAL_RUNS: 0,
            ATTR_RECENT_RUNS: [],
            ATTR_LAST_RUN_DATE: None,
            ATTR_LAST_RUN_TIME: None,
            ATTR_LAST_RUN_POSITION: None,
            ATTR_LAST_RUN_EVENT: None,
            ATTR_PERSONAL_BEST: None,
            ATTR_AVERAGE_TIME: None,
        }
        
        try:
            # Extract total runs from h3 tag like "6 parkruns total"
            h3_total = soup.find('h3', string=lambda text: text and 'parkruns total' in text)
            if h3_total:
                text = h3_total.get_text()
                runs_match = re.search(r'(\d+)\s+parkruns total', text)
                if runs_match:
                    data[ATTR_TOTAL_RUNS] = int(runs_match.group(1))
            
            # Find all tables
            tables = soup.find_all('table')
            
            if len(tables) >= 1:
                # First table: Most Recent parkruns
                # Headers: Event, Run Date, Gender Pos, Overall Position, Time, Age Grade
                recent_table = tables[0]
                tbody = recent_table.find('tbody')
                if tbody:
                    rows = tbody.find_all('tr')
                    recent_runs = []
                    
                    for i, row in enumerate(rows[:10]):  # Get last 10 runs
                        cells = row.find_all('td')
                        if len(cells) >= 6:  # Event, Run Date, Gender Pos, Overall Position, Time, Age Grade
                            try:
                                # Extract event name from link
                                event_cell = cells[0]
                                event_link = event_cell.find('a')
                                event = event_link.get_text().strip() if event_link else event_cell.get_text().strip()
                                
                                # Extract date from link  
                                date_cell = cells[1]
                                date_link = date_cell.find('a')
                                date = date_link.get_text().strip() if date_link else date_cell.get_text().strip()
                                
                                run_data = {
                                    'event': event,
                                    'date': date,
                                    'gender_position': cells[2].get_text().strip(),
                                    'overall_position': cells[3].get_text().strip(), 
                                    'time': cells[4].get_text().strip(),
                                    'age_grade': cells[5].get_text().strip(),
                                }
                                recent_runs.append(run_data)
                                
                                # Set last run data (first row is most recent)
                                if i == 0:
                                    data[ATTR_LAST_RUN_DATE] = run_data['date']
                                    data[ATTR_LAST_RUN_TIME] = run_data['time']
                                    data[ATTR_LAST_RUN_POSITION] = run_data['overall_position']
                                    data[ATTR_LAST_RUN_EVENT] = run_data['event']
                            except (IndexError, ValueError):
                                continue
                    
                    data[ATTR_RECENT_RUNS] = recent_runs
            
            if len(tables) >= 2:
                # Second table: Event Summaries - contains personal best
                # Headers: Event, parkruns, Best Gender Position, Best Position Overall, Best Time
                summary_table = tables[1]
                tbody = summary_table.find('tbody')
                if tbody:
                    # Look for the best time in the summary table
                    rows = tbody.find_all('tr')
                    if rows:
                        first_row = rows[0]
                        cells = first_row.find_all('td')
                        if len(cells) >= 5:  # Event, parkruns, Best Gender Position, Best Position Overall, Best Time
                            best_time_cell = cells[4]
                            # Look for span with class "pretty-time" or just get text
                            time_span = best_time_cell.find('span', class_='pretty-time')
                            if time_span:
                                data[ATTR_PERSONAL_BEST] = time_span.get_text().strip()
                            else:
                                data[ATTR_PERSONAL_BEST] = best_time_cell.get_text().strip()
            
            # Calculate average time from recent runs
            if data[ATTR_RECENT_RUNS]:
                valid_times = []
                for run in data[ATTR_RECENT_RUNS]:
                    time_str = run.get('time', '')
                    if ':' in time_str:
                        try:
                            # Convert MM:SS to total seconds
                            parts = time_str.split(':')
                            if len(parts) == 2:
                                minutes, seconds = int(parts[0]), int(parts[1])
                                total_seconds = minutes * 60 + seconds
                                valid_times.append(total_seconds)
                        except ValueError:
                            continue
                
                if valid_times:
                    data[ATTR_AVERAGE_TIME] = self._seconds_to_time_str(sum(valid_times) // len(valid_times))
        
        except Exception as err:
            _LOGGER.warning("Error parsing Parkrun data: %s", err)
        
        return data
    
    def _seconds_to_time_str(self, seconds: int) -> str:
        """Convert seconds to MM:SS format."""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"


class ParkrunSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a Parkrun sensor."""

    def __init__(
        self,
        coordinator: ParkrunDataUpdateCoordinator,
        user_id: str,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._user_id = user_id
        self._name = name
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{user_id}"
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_native_unit_of_measurement = "runs"

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        return self.coordinator.data.get(ATTR_TOTAL_RUNS, 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            key: value
            for key, value in self.coordinator.data.items()
            if key != ATTR_TOTAL_RUNS
        }

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        return "mdi:run"
