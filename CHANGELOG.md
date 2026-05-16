# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New `NONE` preset entry (`– (manuell)`) lets users keep their manual values
  instead of being forced into one of the named presets.

### Changed
- `_NAME_CANDIDATES` in `rod_link` no longer lists hyphenated module names —
  Python cannot import those, so they were dead entries.
- `create_sleeve_data` no longer returns `inner_diameter`. The value was
  unused by the builder and trivially derivable from `diameter_mm + clearance`.
- `__init__.py` resolves `ui_panel.classes` dynamically inside
  `register` / `unregister` instead of capturing a stale snapshot at
  import time.

### Fixed
- Preset values (`flange`, `wall`, `outer_add`, `clearance`) are now actually
  applied when building a sleeve. Previously the preset selection was ignored
  and the manual property values were always used — most visibly the
  "Mit Flansch" preset produced no flange.
- The thread cutter is now removed in a `try/finally` block so a failing
  boolean apply no longer leaves an orphan cutter mesh in the scene.

## [1.4.0] — Blender 4.0+

- Initial public release with Rod-engine integration, presets,
  hex/round outer shape, optional flange, multi-start and left-hand threads.
