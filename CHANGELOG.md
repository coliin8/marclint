# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.0.4] - 2026-01-18

- Language-aware article validation using 008 field language code (positions 35-37)
- Expanded article dictionary with support for 20 languages: Afrikaans, Catalan, Danish, Dutch, English, Esperanto, French, German, Galician, Hungarian, Icelandic, Irish, Italian, Maltese, Norwegian, Portuguese, Spanish, Swedish, Welsh, and Yiddish
- New articles added: Dutch (de, een, het), Afrikaans ('n), Hungarian (az, egy), Icelandic (hinn, hin, hið, etc.), Irish (na), Welsh (y, yr), Yiddish (di, dos), Esperanto (la), French (du), Italian (i), Scandinavian (det, et, ett)

### Changed
- Article validation now checks record language before flagging non-filing indicator issues
- Articles dictionary now uses lists instead of space-delimited strings for language codes
- Article validation skips judgment for languages not in the supported languages list

## [0.0.3] - 2026-01-18

### Added
- Leader validation (`check_leader()`) for positions 05, 06, 07, 08, 09, 17, 18, 19
- Control field 008 validation (`check_008()`) for length, dates, country codes, language codes, and cataloging source
- Multi-record batch processing with `check_records()` method
- `RecordResult` class for structured batch processing results
- Record identification in warnings via `record_id` field in `MarcWarning`
- Automatic record ID extraction from 001 field
- Leader validation code tables in `code_data.py`
- CLI `--format json` option for JSON output
- CLI `--quiet` option to suppress summary output
- CLI `--use-index` option for records without 001 field
- CLI now shows record IDs from 001 field instead of sequential numbers

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
