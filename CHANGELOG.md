# CHANGELOG



## v0.1.0 (2025-07-03)

### Build

* build: add development infrastructure

- Updated pyproject.toml with dev, viz, docs, and all dependency groups
- Added pytest.ini configuration for test discovery
- Added .pre-commit-config.yaml for code quality checks
- Updated .gitignore with Python and development patterns
- Added CLAUDE.md for AI assistant guidance
- Added IMPLEMENTATION_PLAN.md outlining future features

Sets up professional development workflow with automated quality checks. ([`9201f04`](https://github.com/ayenpure/zarr-utils/commit/9201f04cdd5ca7bc0114090c7a135ac437ff56cc))

### Ci

* ci: add GitHub Actions workflows

- ci.yml: Comprehensive CI pipeline
  - Tests on Python 3.9, 3.10, 3.11
  - Multiple OS support (Ubuntu, Windows, macOS)
  - Code quality checks (ruff, mypy)
  - Test coverage reporting
  - Documentation build verification

- release.yml: Automated semantic release
  - Triggered on main branch pushes
  - Version bumping and changelog generation
  - PyPI publishing
  - GitHub release creation

Establishes automated quality assurance and release process. ([`8531230`](https://github.com/ayenpure/zarr-utils/commit/8531230347c0e9648725bee4f6868effb241a3b4))

### Documentation

* docs: add comprehensive documentation with MkDocs

- MkDocs configuration with Material theme
- Read the Docs integration (.readthedocs.yaml)
- Complete documentation structure:
  - Getting Started guides (installation, quickstart, examples)
  - User guides for each feature
  - API reference (auto-generated from docstrings)
  - Development guides (contributing, testing, changelog)
- Updated README with badges and quick start
- Ready for deployment to readthedocs.io

Provides professional documentation for users and contributors. ([`812b119`](https://github.com/ayenpure/zarr-utils/commit/812b11970fdb6130af51c864c5c30619a7779de4))

### Feature

* feat: add debugging and diagnostic tools

- ZarrDebugger: Context manager for operation tracking and timing
- diagnose_zarr_store(): Comprehensive diagnostics with performance metrics
- explain_zarr_error(): User-friendly error explanations with solutions
- enable_debug_mode(): Verbose debugging for development
- Full test coverage for debugging utilities

Provides better error messages and helps diagnose common Zarr issues. ([`0cf1f73`](https://github.com/ayenpure/zarr-utils/commit/0cf1f73616a06e99728fca0e2a34e298ede7b170))

* feat: add metadata management utilities

- consolidate_metadata(): Create/repair .zmetadata for better performance
- validate_metadata(): Check metadata integrity and completeness
- repair_metadata(): Auto-fix common metadata issues
- Comprehensive test coverage for all metadata operations

Solves the common &#39;KeyError: .zmetadata&#39; issue and improves remote store performance. ([`fc63d4b`](https://github.com/ayenpure/zarr-utils/commit/fc63d4bc90cd22841f356911c2e23a6b2cba8e26))

* feat: add Zarr v2/v3 compatibility layer

- Automatic version detection (IS_ZARR_V3)
- consolidate_metadata() wrapper handling metadata_key parameter
- create_array_compat() for unified array creation API
- open_array/group_with_storage_options() for proper storage handling
- get_array_compressor() abstracts v2/v3 compressor access
- access_store_item() and store_contains() for store API differences

This provides a foundation for supporting both Zarr v2 and v3 throughout the codebase. ([`a45f6fe`](https://github.com/ayenpure/zarr-utils/commit/a45f6fee7f6c805cdacc6ecffdb0ce95e168c363))

### Fix

* fix(initial commit): Adding initial APIs ([`80cfd01`](https://github.com/ayenpure/zarr-utils/commit/80cfd0135614cac9cf5b04fe22fe2b2e5b3b8005))

### Refactor

* refactor: rename convert.py to visualization.py and update modules

- Renamed convert.py to visualization.py for clarity
- Updated all modules to use compatibility layer
- Enhanced inspect.py with type hints and better error handling
- Improved xarray.py with proper coordinate handling and 2D array support
- Added comprehensive test suite for all modules
- Updated examples to use new imports
- Added __all__ exports to __init__.py for clean public API

All modules now support both Zarr v2 and v3 seamlessly. ([`3dc7b22`](https://github.com/ayenpure/zarr-utils/commit/3dc7b227be243a8ecad43a56957f58a87ee255ca))

### Unknown

* Initial commit ([`3b8e9e5`](https://github.com/ayenpure/zarr-utils/commit/3b8e9e5f0fe4e9a9fe5b231a52f535d7401783e4))
