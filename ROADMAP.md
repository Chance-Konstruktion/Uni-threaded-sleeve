# Uni-threaded-sleeve Roadmap

**Audit baseline:** 2026-10-26  
**Version metadata:** 1.5.0  
**Dependency:** [Uni-threaded-rod](https://github.com/Chance-Konstruktion/Uni-threaded-rod)

The shared contract and cross-repository milestones are maintained in the [Rod + Sleeve master roadmap](https://github.com/Chance-Konstruktion/Uni-threaded-rod/blob/main/ROADMAP.md). This file tracks implementation work specific to Sleeve.

## Current architecture

Sleeve delegates standards, parameter resolution, profile generation, tolerance defaults, and thread mesh generation to rod_link.py. Sleeve owns its outer body, presets, Boolean cutters, and flange geometry. Do not copy the Rod standards database into this repository.

## Priority 0 — Geometry correctness and validation

- [x] **SLEEVE-001 — Flanges must not cap the bore.** Add and fuse flange geometry before the thread-cut Boolean. Headless Blender regression checks must prove the bore stays open through both flanges and the resulting mesh is manifold.
- [x] **SLEEVE-002 — Validate direct API calls.** Direct API and builder calls validate finite positive length/diameter, wall thickness >= 1 mm, non-negative outer addition, bounded clearance, valid start count/handedness, and positive resulting dimensions.
- [x] **SLEEVE-003 — Temporary-object cleanup.** Boolean/mesh failure paths remove cutters, both flange operands, and partial sleeve bodies; unit failure-cleanup regression coverage is in place.
- [ ] **SLEEVE-004 — CI recency.** The latest visible successful action for main is dated 2026-07-15. Require a new green unit, real-Rod integration, and headless Blender run before release.

## Priority 1 — Rod integration contract

- [x] **SLEEVE-101 — Pitch override consistency.** The effective pitch, returned profile_points and recalculated mechanics must all describe the same geometry; validated in unit and real-Rod integration tests.
- [x] **SLEEVE-102 — Dependency diagnostics.** Keep lazy imports safe during add-on discovery; the data API checks required Rod APIs without importing Blender-only mesh modules, while object generation also requires the mesh builder and reports actionable errors.
- [ ] **SLEEVE-103 — Integration contract tests.** Run Sleeve against the actual Rod checkout, test every standard's representative token, verify a non-degenerate internal profile, and add reference-dimension tests where exact values are known.
- [x] **SLEEVE-104 — API compatibility.** Required Rod functions are capability-checked before mesh generation, and compatibility requirements are documented.

## Priority 2 — Finish quality and delivery

- [x] **SLEEVE-201 — Preset validation.** Ensure every preset's standard exists in Rod, all preset values are applied, and effective dimensions are reported to users.
- [ ] **SLEEVE-202 — Geometry matrix.** Cover cylinder and hex outer bodies, one and two flanges, multiple starts, left-hand threads, clearance presets, pitch override, and tapered profiles in automated smoke or integration tests.
- [ ] **SLEEVE-203 — Packaging test.** Install the actual distribution ZIP in a clean Blender environment and check that hyphenated folder names and Rod discovery behave as documented.
- [ ] **SLEEVE-204 — Release synchronization.** Update bl_info, README, CHANGELOG, and the master roadmap together. Document exactly which Rod revision was tested for a Sleeve release.

## Acceptance gates

A change is ready to merge only when unit tests and real-Rod integration tests pass. Changes affecting geometry also require a fresh headless Blender smoke test. A release is not validated based only on an older green run.
