# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.2] - 2025-12-25

### Added
- Structured warning objects (`MarcWarning`) for API integration and automation
- Position tracking for repeating fields in warnings
- `warnings_structured()` method for programmatic access to warning data
- JSON serialization support for warnings via `to_dict()` method
- Test coverage reporting with pytest-cov and codecov integration

## [0.0.1] - 2025-12-17

### Added
- Initial release - Python port of Perl MARC::Lint
- MARC21 record validation with comprehensive field checks
- ISBN validation (field 020) using python-stdnum
- ISSN validation (field 022) using python-stdnum
- Language code validation (field 041) with ISO 639-2 codes
- Geographic area code validation (field 043) with MARC Geographic Areas
- Article/non-filing indicator validation for title fields (130, 240, 245, 630, 730, 830)
- Title field (245) validation with punctuation and subfield order checks
- Alternate graphic representation (880) field validation
- CLI tool `marc-lint` for batch processing MARC files
- Comprehensive test suite (107 tests across multiple Python versions)
- Support for Python 3.10, 3.11, 3.12, 3.13, and 3.14
- Type hints throughout the codebase
- Field repeatability validation
- Indicator validation for all applicable fields
- Subfield validation and repeatability checks
- GitHub Actions CI/CD workflows
- Documentation (README, CONTRIBUTING, SECURITY, CHANGELOG)
- Proper copyright attribution to original MARC::Lint authors
