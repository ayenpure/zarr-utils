# Changelog

All notable changes to zarr-utils will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation using MkDocs
- Full Zarr v2/v3 compatibility layer
- Metadata consolidation and validation tools
- Debugging utilities with helpful error messages
- Type hints throughout the codebase
- Pre-commit hooks for code quality
- GitHub Actions CI/CD pipeline
- Comprehensive test suite with pytest

### Changed
- Renamed `convert.py` to `visualization.py` for clarity
- Enhanced all functions with better error handling
- Improved xarray integration with proper coordinate handling

### Fixed
- Storage options handling for local paths
- 2D array handling in xarray integration
- Compatibility issues between Zarr versions

## [0.1.0] - 2024-01-01

### Added
- Initial release
- Basic Zarr store inspection (`list_zarr_arrays`, `inspect_zarr_store`)
- Xarray integration (`open_xarray`, `get_voxel_spacing`)
- VTK visualization support (`wrap_vtk`, `to_vti`)
- Support for local and remote (S3) Zarr stores
- Basic examples and documentation

### Known Issues
- Limited Zarr v3 support
- No automated testing
- Minimal error handling

## Development Roadmap

### v0.2.0 (Planned)
- [ ] Chunk optimization analyzer
- [ ] Data integrity checker
- [ ] Performance profiler
- [ ] Safe concurrent write wrapper

### v0.3.0 (Planned)
- [ ] Cloud storage optimization utilities
- [ ] Format conversion tools with progress tracking
- [ ] ML framework adapters (PyTorch/TensorFlow)

### v1.0.0 (Future)
- [ ] Stable API
- [ ] Complete documentation
- [ ] Performance benchmarks
- [ ] Integration examples

## Version History

- **0.1.0** - Initial release with basic functionality
- **0.0.1** - Pre-release development version

[Unreleased]: https://github.com/yourusername/zarr-utils/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/zarr-utils/releases/tag/v0.1.0