# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New `NONE` preset entry (`– (manuell)`) lets users keep their manual values
  instead of being forced into one of the named presets.
- New `pitch_override` property in the UI / `create_sleeve_data`. Set it to a
  value > 0 to use a custom thread pitch (e.g. M10 x 1.0 instead of the Rod
  default 1.5); 0 keeps the Rod-provided pitch.
- Unit test suite under `tests/` (41 tests, mocked `bpy` and Rod) plus a
  GitHub Actions workflow that compiles every module and runs the suite on
  Python 3.10 / 3.11 / 3.12.

### Changed
- A preset that names a `standard` Rod does not know is now ignored
  instead of being passed through; the manually selected standard is kept.
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
