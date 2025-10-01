# Parkrun Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/benfl3713/ha_parkrun.svg)](https://github.com/benfl3713/ha_parkrun/releases/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Home Assistant custom component to track your Parkrun statistics by scraping your Parkrun profile page.

## Features

- Track total number of Parkrun events completed
- Monitor your most recent run details (date, time, position, event)
- View your personal best time and average time
- Separate sensors for each metric allow for better historical tracking and charting
- Automatic updates every hour

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL: `https://github.com/benfl3713/ha_parkrun`
5. Select "Integration" as the category
6. Click "ADD"
7. Find "Parkrun" in the integration list and click "Install"
8. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/parkrun` folder from this repository
2. Place it in your `custom_components` directory in your Home Assistant config directory
3. Restart Home Assistant

## Configuration

1. In Home Assistant, go to Configuration → Integrations
2. Click the "+" button to add a new integration
3. Search for "Parkrun" and select it
4. Enter your Parkrun user ID (the number from your Parkrun profile URL)
   - For example, if your profile URL is `https://www.parkrun.org.uk/parkrunner/1234567/`, your user ID is `1234567`
5. Optionally customize the sensor name
6. Click "Submit"

## Usage

Once configured, the integration creates multiple sensor entities for better historical tracking:

- `sensor.parkrun_total_runs` - Total number of runs completed
- `sensor.parkrun_last_run_time` - Your time for the most recent run
- `sensor.parkrun_last_run_date` - Date of your most recent run
- `sensor.parkrun_last_run_position` - Your position in the most recent run
- `sensor.parkrun_last_run_event` - The Parkrun event name for your most recent run
- `sensor.parkrun_personal_best` - Your best recorded time
- `sensor.parkrun_average_time` - Your average time across recent runs

**Note**: If you customize the sensor name during configuration (e.g., "John's Parkrun"), the entity IDs will be prefixed accordingly (e.g., `sensor.johns_parkrun_total_runs`).

## Example Automation

```yaml
automation:
  - alias: "New Parkrun PB Notification"
    trigger:
      - platform: state
        entity_id: sensor.parkrun_personal_best
    condition:
      - condition: template
        value_template: "{{ trigger.from_state.state != trigger.to_state.state }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "New Parkrun PB!"
          message: "Congratulations! New personal best: {{ states('sensor.parkrun_personal_best') }}"
```

## Lovelace Card Example

```yaml
type: entities
entities:
  - entity: sensor.parkrun_total_runs
    name: Total Runs
  - entity: sensor.parkrun_last_run_date
    name: Last Run Date
  - entity: sensor.parkrun_last_run_time
    name: Last Run Time
  - entity: sensor.parkrun_last_run_position
    name: Last Run Position
  - entity: sensor.parkrun_personal_best
    name: Personal Best
  - entity: sensor.parkrun_average_time
    name: Average Time
  - entity: sensor.parkrun_last_run_event
    name: Last Run Event
title: My Parkrun Stats
```

## Data Source

This integration scrapes data from the Parkrun UK website. It respects the site's structure and updates responsibly with a default interval of 60 minutes.

## Troubleshooting

- Ensure your Parkrun profile is public and accessible
- Check that your user ID is correct
- If data isn't updating, check the Home Assistant logs for any errors
- The integration requires an internet connection to access the Parkrun website

## Contributing

Issues and pull requests are welcome! Please check the [issue tracker](https://github.com/benfl3713/ha_parkrun/issues) before submitting new issues.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
