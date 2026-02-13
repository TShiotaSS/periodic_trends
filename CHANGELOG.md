# Changelog

All notable changes in this fork are documented in this file.

## [0.2.1] - 2026-02-13

### Added

- Added `--unique-structure` option to `xyz_to_periodic_table.py`.
- Added frame de-duplication by `info['structure_name']` for multi-frame XYZ/EXTXYZ inputs.
- Added runtime output to show counted frames after de-duplication.

### Changed

- Updated `README.md` with usage and notes for `--unique-structure`.

## [0.2.0] - 2026-02-13

### Added

- Added `xyz_to_periodic_table.py` utility script.
- Added XYZ-to-element-count workflow using `ase.io.read(...)`.
- Added periodic-table visualization pipeline from element counts via `periodic_trends.plotter(...)`.
- Added PNG export with configurable `--dpi` and HTML export support.

### Changed

- Updated `README.md` with usage and dependency notes for the XYZ utility.
- Added explicit change-history reference in `README.md`.

### Notes

- PNG export uses bokeh `export_png(...)` and requires `selenium` plus a browser driver.
