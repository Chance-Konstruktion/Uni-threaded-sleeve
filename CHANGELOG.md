# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Preset values (`flange`, `wall`, `outer_add`, `clearance`) are now actually
  applied when building a sleeve. Previously the preset selection was ignored
  and the manual property values were always used — most visibly the
  "Mit Flansch" preset produced no flange.

## [1.4.0] — Blender 4.0+

- Initial public release with Rod-engine integration, presets,
  hex/round outer shape, optional flange, multi-start and left-hand threads.
