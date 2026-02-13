# Changelog

All notable changes in this fork are documented in this file.

## [0.2.15] - 2026-02-13

### Added

- Added `--all-black-text` option to `xyz_to_periodic_table.py` to force all
  periodic-table labels to black.

### Changed

- Updated `README.md` examples and argument docs for `--all-black-text`.

## [0.2.14] - 2026-02-13

### Added

- Added `--log-fraction` option to `xyz_to_periodic_table.py` to visualize
  `log10(element_fraction)`.

### Changed

- Updated `xyz_to_periodic_table.py` default CSV naming for log-fraction mode to
  `<output_stem>_fraction_log.csv`.
- Updated `xyz_to_periodic_table.py` colorbar caption in log-fraction mode to
  `log(Element fraction)`.
- Added validation to prevent combining `--log-fraction` with `--log-scale`.
- Updated `README.md` docs for `--log-fraction`.

## [0.2.13] - 2026-02-13

### Added

- Added `--fraction` option to `xyz_to_periodic_table.py` to visualize
  `element_fraction = element_count / max(element_count)`.

### Changed

- Updated `xyz_to_periodic_table.py` colorbar caption logic:
  `Element fraction` is used only when `--fraction` is enabled (otherwise `Count`).
- Updated default CSV export behavior for `--fraction` mode to
  `<output_stem>_fraction.csv`.
- Updated `README.md` examples and argument docs for fraction mode.

## [0.2.12] - 2026-02-13

### Added

- Added CSV input mode to `xyz_to_periodic_table.py`:
  `.csv` inputs are now accepted for plotting using `Element,element_count` data.

### Changed

- CSV export is now enabled by default in `xyz_to_periodic_table.py`:
  counts are written to `<output_stem>_counts.csv` unless `--save-csv` is specified.
- Updated runtime frame summary behavior for CSV input (`N/A`) vs XYZ input.
- Updated `README.md` examples and argument docs for default CSV output and CSV input mode.

## [0.2.11] - 2026-02-13

### Added

- Added `--save-csv` option to `xyz_to_periodic_table.py` to export element counts as CSV.

### Changed

- Updated runtime output in `xyz_to_periodic_table.py` to always print frame summary including total frame count.
- Updated `README.md` examples and argument docs for CSV export and frame summary output.

## [0.2.10] - 2026-02-13

### Added

- Added `--color-min` and `--color-max` options to `xyz_to_periodic_table.py`.
- Added CLI-to-plotter wiring for fixed colorbar ranges (`color_min` / `color_max`).

### Changed

- Updated `README.md` examples and argument docs for colorbar range control.

## [0.2.9] - 2026-02-13

### Changed

- Updated `--print-data` output formatting in `xyz_to_periodic_table.py` to use integer labels (`float_decimals=0`).

## [0.2.8] - 2026-02-13

### Added

- Added `--print-data` option to `xyz_to_periodic_table.py`.
- Added CLI-to-plotter wiring for printing per-cell count labels (`print_data=True`).

### Changed

- Updated `README.md` examples and argument docs for in-cell count labels.

## [0.2.7] - 2026-02-13

### Changed

- Updated colorbar title styling in `xyz_to_periodic_table.py`:
  `Count` label is now rendered with normal (non-italic) style and larger font size.

## [0.2.6] - 2026-02-13

### Added

- Added `--cmap` option to `xyz_to_periodic_table.py` to control colormap from CLI.
- Added validation for colormap names via `matplotlib.colormaps`.

### Changed

- Updated `README.md` examples and argument docs for colormap selection.

## [0.2.5] - 2026-02-13

### Changed

- Added adaptive text-color rendering in `xyz_to_periodic_table.py`:
  black text on light cells and white text on dark cells.

## [0.2.4] - 2026-02-13

### Changed

- Updated `--exclude-elements` rendering to show excluded cells in white with a black border.
- Added post-plot glyph styling in `xyz_to_periodic_table.py` so excluded elements are easier to identify.

## [0.2.3] - 2026-02-13

### Added

- Added `--exclude-elements` option to `xyz_to_periodic_table.py`.
- Added counting-time exclusion of specified element symbols.
- Added white rendering for excluded elements via `special_elements`/`special_color`.

### Changed

- Updated `README.md` examples and argument docs for `--exclude-elements`.

## [0.2.2] - 2026-02-13

### Added

- Added `--log-scale` option to `xyz_to_periodic_table.py`.
- Added CLI-to-plotter wiring for logarithmic colorbar rendering (`log_scale=True`).

### Changed

- Updated `README.md` examples and argument docs for `--log-scale`.

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
