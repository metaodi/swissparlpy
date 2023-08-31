# Changelog
All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project follows [Semantic Versioning](http://semver.org/).

## [Unreleased]
### Added
- Support for server-side pagination (transparent to the user)
- `ResultVeryLargeWarning` to warn developers about very large queries
- Logging to help with debugging
- Add pre-commit configuration

### Changed
- Use `black` code style

## [0.2.1] - 2022-01-31
### Fixed
- In order to fix issue #17 a bug in pyodata had to be fixed. pyodata 1.9.0 contains the bugfix and is now specified as the minimum version.

## [0.2.0] - 2021-10-14
### Added
- Jupyter notebook with examples
- New examples for advanced filters
- Support for more advanced filters

### Changed
- Update README with examples

## [0.1.1] - 2021-09-27
### Fixed
- Typo in publish workflow

## [0.1.0] - 2021-09-27
### Added
- Test with fixtures
- Linter for all code
- Usage example in README

### Fixed
- Fixed `get_variables` call
- Make sure `get_tables` returns a list


## [0.0.2] - 2021-09-27
### Added
- Added CHANGELOG file

### Changed
- Use flit to manage pypi package


## [0.0.1] - 2021-09-26
### Added
- Initial release of swissparlpy


# Categories
- `Added` for new features.
- `Changed` for changes in existing functionality.
- `Deprecated` for once-stable features removed in upcoming releases.
- `Removed` for deprecated features removed in this release.
- `Fixed` for any bug fixes.
- `Security` to invite users to upgrade in case of vulnerabilities.

[Unreleased]: https://github.com/metaodi/swissparlpy/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/metaodi/swissparlpy/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/metaodi/swissparlpy/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/metaodi/swissparlpy/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/metaodi/swissparlpy/compare/v0.0.2...v0.1.0
[0.0.2]: https://github.com/metaodi/swissparlpy/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/metaodi/swissparlpy/releases/tag/v0.0.1
