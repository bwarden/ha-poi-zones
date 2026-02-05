# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-02-05

### Added
- **Zone name prefix/customization** (REQUIRED): Configure custom prefixes for zone entities to avoid cluttering the entity list
  - **Prefix is now required** for better entity organization
  - Simple default: just the POI type (e.g., `hospital`)
  - Fully customizable to your preference (e.g., `nyc_hospital`, `home_hospital`, `my_hospital`)
  - Results in clean entity names: `zone.{prefix}_{poi_name}`
  - Example: prefix "hospital" → `zone.hospital_crouse_hospital`
  - Example: prefix "syracuse_hospital" → `zone.syracuse_hospital_crouse_hospital`
  - Prevents 2000+ unprefixed entities
  - **Prioritizes user customization** over automatic naming
- GitHub Actions for automated releases
  - Automatic release creation on version tags
  - Auto-packaged integration ZIP files
  - Consistent release notes

### Changed
- Zone entity naming now includes configurable prefix by default
- Improved zone ID generation for better organization
- Updated sensor attributes to include both original and prefixed names

### Fixed
- Zone entity organization and naming consistency

## [1.0.0] - 2026-02-04

### Added
- Initial release
- 40+ POI types from OpenStreetMap
- Automatic zone creation
- Dynamic radius sizing for healthcare facilities (130m-280m)
- Generic automation templates
- Weekly auto-updates
- Hospital visit notification automation example
- Support for:
  - Healthcare (hospitals, urgent care, clinics, pharmacies, dentists, vets)
  - Education (schools, universities, daycares)
  - Transportation (airports, train stations, gas stations, EV charging)
  - Food & Drink (restaurants, fast food, cafes, bars, grocery stores)
  - Services (banks, post offices, libraries, hotels)
  - Public Safety (police, fire stations)
  - Recreation (parks, gyms, movie theaters)
  - And more!

[1.1.0]: https://github.com/DEADSEC-SECURITY/ha-poi-zones/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/DEADSEC-SECURITY/ha-poi-zones/releases/tag/v1.0.0
