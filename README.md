# POI Zones for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Automatically create Home Assistant zones for Points of Interest (POIs) near your location using OpenStreetMap data.

## Features

- 🏥 **40+ POI Types**: Hospitals, urgent care, schools, restaurants, gas stations, and more
- 📍 **Automatic Zone Creation**: Creates Home Assistant zones for all discovered POIs
- 🎯 **Dynamic Radius Sizing**: Intelligent zone sizing based on facility size (hospitals, urgent care)
- 🔄 **Auto-Updates**: Refreshes POI data weekly
- 🌍 **OpenStreetMap**: Uses free OpenStreetMap data via Overpass API
- 🔔 **Automation Ready**: Easily create automations when people enter POI zones

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the 3 dots in the top right
3. Select "Custom repositories"
4. Add this repository URL: `https://github.com/DEADSEC-SECURITY/ha-poi-zones`
5. Category: Integration
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/poi_zones` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "POI Zones"
4. Enter:
   - **City**: Your city name (e.g., "New York, NY")
   - **POI Type**: Select from 40+ available types
   - **Search Radius** (optional): Distance in km to search from city center
   - **Zone Radius** (optional): Default radius for created zones in meters

## Available POI Types

### Healthcare
- Hospitals (with dynamic sizing)
- Urgent Care (with dynamic sizing)
- Clinics
- Pharmacies
- Doctor's Offices
- Dentists
- Veterinary Clinics
- Nursing Homes

### Education
- Schools (K-12)
- Universities & Colleges
- Childcare & Daycares

### Transportation
- Airports
- Train Stations
- Gas Stations
- EV Charging Stations
- Car Washes
- Auto Repair Shops

### Food & Drink
- Restaurants
- Fast Food
- Cafes & Coffee Shops
- Bars & Pubs
- Grocery Stores

### Services
- Banks
- Post Offices
- Libraries
- Hotels

### Public Safety
- Police Stations
- Fire Stations

### Recreation
- Parks
- Movie Theaters
- Gyms & Fitness Centers

### Religious
- Places of Worship

## Dynamic Zone Sizing

For hospitals and urgent care facilities, the integration automatically adjusts zone radius based on:
- **Number of beds** (if available in OpenStreetMap)
- **Building footprint** (node/way/relation)
- **Healthcare type** (hospital vs clinic)
- **Emergency status**

This ensures small clinics get smaller zones (100-130m) while major medical centers get larger zones (230-280m).

## Sensors

Each POI integration creates a sensor entity:
- **State**: Number of POIs found
- **Attributes**:
  - `zone_ids`: List of all zone IDs created
  - `locations`: Detailed information for each POI
  - `city`: City name
  - `poi_type`: Type of POIs
  - Plus coordinates, names, addresses, phone numbers, websites, etc.

## Example Automations

### Hospital Visit Notification

Get notified when someone has been at a hospital for over 30 minutes:

```yaml
automation:
  - alias: "Hospital Visit Alert"
    trigger:
      - platform: template
        value_template: >
          {% set poi_zones = namespace(ids=[]) %}
          {% for sensor in states.sensor | selectattr('attributes.poi_type', 'defined') %}
            {% if sensor.attributes.poi_type in ['hospital', 'urgent_care'] %}
              {% set poi_zones.ids = poi_zones.ids + sensor.attributes.zone_ids %}
            {% endif %}
          {% endfor %}
          {{ expand(states.person)
             | selectattr('state', 'in', poi_zones.ids)
             | list | count > 0 }}
        for:
          minutes: 30
    action:
      - service: notify.notify
        data:
          title: "🏥 Healthcare Visit Alert"
          message: >
            {% set poi_zones = namespace(ids=[]) %}
            {% for sensor in states.sensor | selectattr('attributes.poi_type', 'defined') %}
              {% if sensor.attributes.poi_type in ['hospital', 'urgent_care'] %}
                {% set poi_zones.ids = poi_zones.ids + sensor.attributes.zone_ids %}
              {% endif %}
            {% endfor %}
            {% set people_at_facility = expand(states.person)
               | selectattr('state', 'in', poi_zones.ids)
               | list %}
            {% for person in people_at_facility %}
              {{ person.name }} has been at {{ state_attr('zone.' + person.state, 'friendly_name') }} for over 30 minutes.
            {% endfor %}
```

### School Arrival Notification

Get notified when kids arrive at school:

```yaml
automation:
  - alias: "School Arrival"
    trigger:
      - platform: zone
        entity_id: person.child
        zone: zone.school_name
        event: enter
    action:
      - service: notify.mobile_app
        data:
          message: "{{ trigger.to_state.attributes.friendly_name }} arrived at school"
```

## Data Source

This integration uses:
- **Nominatim** for geocoding city names
- **Overpass API** for querying OpenStreetMap POI data

Data is refreshed weekly by default. All data comes from OpenStreetMap contributors and is available under the ODbL license.

## Troubleshooting

### No POIs Found

- Check that the city name is correct (try adding state/country)
- Some POI types may not be well-tagged in OpenStreetMap for your area
- Try increasing the search radius

### Zones Not Created

- Ensure the "Zone" integration is enabled in Home Assistant
- Check Home Assistant logs for errors
- Zones are created/updated on integration reload or HA restart

### Wrong Zone Locations

- OpenStreetMap data quality varies by location
- Building entrances vs centers may cause slight offsets
- The 30m positioning buffer helps account for this

## Contributing

Contributions are welcome! Please open an issue or pull request on GitHub.

## License

This project is licensed under the MIT License.

## Credits

- OpenStreetMap contributors for POI data
- Nominatim for geocoding
- Overpass API for OSM queries
