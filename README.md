# marc-lint

[![CI](https://github.com/coliin8/marclint/actions/workflows/ci.yml/badge.svg)](https://github.com/coliin8/marclint/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/marc-lint.svg)](https://badge.fury.io/py/marc-lint)
[![Python versions](https://img.shields.io/pypi/pyversions/marc-lint.svg)](https://pypi.org/project/marc-lint/)
[![codecov](https://codecov.io/gh/coliin8/marclint/branch/main/graph/badge.svg)](https://codecov.io/gh/coliin8/marclint)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python port of the Perl [MARC::Lint](https://metacpan.org/dist/MARC-Lint) module for validating MARC21 bibliographic records.

## Features

- ✅ Comprehensive MARC21 validation
- ✅ ISBN/ISSN validation using industry-standard algorithms
- ✅ Language and geographic code validation
- ✅ Article/non-filing indicator validation
- ✅ Command-line tool for batch processing
- ✅ Python 3.10+ support
- ✅ Type hints and comprehensive test coverage

## Installation

```bash
pip install marc-lint
```

Or with uv:
```bash
uv pip install marc-lint
```

## Quick Start

### Command Line Interface

Lint a MARC file and display warnings:

```bash
marc-lint records.mrc
```

Example output:
```
--- Record 1 ---
  020: Subfield a has bad checksum, 123456789X.
  245: Must end with . (period).

--- Record 2 ---
  022: Subfield a has bad checksum, 1234-5678.

============================================================
Processed 2 record(s)
Found 3 warning(s)
```

The CLI exits with status code 0 if no warnings are found, or 1 if warnings are present (useful for CI/CD).

```bash
# Use in CI/CD pipelines
marc-lint catalog.mrc && echo "All records valid!"
```

### Python Library - Basic Usage

```python
from marc_lint import MarcLint
from pymarc import MARCReader

# Create a linter instance
linter = MarcLint()

# Process MARC records
with open('records.mrc', 'rb') as fh:
    reader = MARCReader(fh)
    for record in reader:
        linter.check_record(record)
        
        # Get warnings as strings (backward compatible)
        if linter.warnings():
            print(f"Record has {len(linter.warnings())} warnings:")
            for warning in linter.warnings():
                print(f"  - {warning}")
```

### Python Library - Structured Warnings

For automation and API integration, use structured warnings:

```python
from marc_lint import MarcLint
from pymarc import MARCReader

linter = MarcLint()

with open('records.mrc', 'rb') as fh:
    reader = MARCReader(fh)
    for record in reader:
        linter.check_record(record)
        
        # Get structured warning objects
        for warning in linter.warnings_structured():
            print(f"Field: {warning.field}")
            print(f"Message: {warning.message}")
            if warning.subfield:
                print(f"Subfield: {warning.subfield}")
            if warning.position is not None:
                print(f"Position: {warning.position + 1}")
```

### Python Library - JSON Output

Export warnings as JSON for APIs:

```python
import json
from marc_lint import MarcLint
from pymarc import MARCReader

linter = MarcLint()

with open('records.mrc', 'rb') as fh:
    reader = MARCReader(fh)
    for record in reader:
        linter.check_record(record)
        
        # Convert to JSON
        warnings_data = [w.to_dict() for w in linter.warnings_structured()]
        print(json.dumps(warnings_data, indent=2))
```

Example JSON output:
```json
[
  {
    "field": "020",
    "message": "has bad checksum, 123456789X.",
    "subfield": "a",
    "position": null
  },
  {
    "field": "245",
    "message": "Must end with . (period).",
    "subfield": null,
    "position": null
  }
]
```

### Python Library - Filtering Warnings

```python
# Filter warnings by field
isbn_warnings = [
    w for w in linter.warnings_structured() 
    if w.field == "020"
]

# Filter by subfield
subfield_a_warnings = [
    w for w in linter.warnings_structured() 
    if w.subfield == "a"
]

# Group by field
from collections import defaultdict
warnings_by_field = defaultdict(list)
for warning in linter.warnings_structured():
    warnings_by_field[warning.field].append(warning)
```

See [STRUCTURED_WARNINGS.md](STRUCTURED_WARNINGS.md) for detailed documentation on structured warnings.

## Validation Rules

### Supported Fields

- **020**: ISBN validation with checksum verification
- **022**: ISSN validation with checksum verification
- **041**: Language codes (ISO 639-2)
- **043**: Geographic area codes (MARC Geographic Areas)
- **130, 240, 630, 730, 830**: Non-filing indicator validation
- **245**: Comprehensive title validation (punctuation, indicators, subfield order)
- **880**: Alternate graphic representation validation
- Plus general field/subfield/indicator validation for all tags

## Architecture

### Files

- `marc_lint.linter.py` – main `MarcLint` class, equivalent and extension to `MARC::Lint`.
- `marc_lint.code_data.py` – translation of the code tables from
  `MARC::Lint::CodeData` (language, geographic area, country codes).
- `marc_lint.field_rules.py` – equivalent to `__DATA__` and `_read_rules` in `MARC::Lint`.

Key behavior mirrored from the Perl module:

- Per-record checks in `MarcLint.check_record`: 1XX-count, required 245,
  field repeatability, indicator validity, subfield legality and
  repeatability, and control-field rules.
- Tag-specific methods `check_020`, `check_041`, `check_043`, `check_245`,
  plus `_check_article` for handling non-filing indicators.
- Add Tag-specific methods `check_022` and will add others in the future.
- Rules for tags are built in `_read_rules` from `RULES_DATA`, which is a
  equivalent to `__DATA__` table in `Lint.pm`.

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/coliin8/marclint.git
cd marclint

# Install dependencies (including dev dependencies)
uv sync --all-groups

# Activate the virtual environment (optional, uv run handles this automatically)
source .venv/bin/activate
```

### Common Development Tasks

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/marc_lint --cov-report=term-missing

# Run tests across all Python versions (3.10-3.14)
uv run tox

# Run linting
uv run tox -e lint

# Auto-format code
uv run tox -e format

# Run specific test file
uv run pytest tests/test_warning.py -v

# Run specific test
uv run pytest tests/test_warning.py::test_warning_basic_creation -v

# Run bump version of project
uv run bump-my-version bump patch
```

### Code Quality

This project uses:
- **pytest** for testing
- **pytest-cov** for coverage reporting
- **ruff** for linting and formatting (via tox)
- **tox** for testing across multiple Python versions

### Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) file for details.

This is a Python port of the original Perl [MARC::Lint](https://metacpan.org/dist/MARC-Lint) module.

## Acknowledgments

- **Bryan Baldus, Ed Summers, and Dan Lester** for the original Perl MARC::Lint module (2001-2011)
- Library of Congress for MARC21 standards and documentation

## Links

- [PyPI](https://pypi.org/project/marc-lint/)
- [GitHub](https://github.com/coliin8/marclint)
- [Issue Tracker](https://github.com/coliin8/marclint/issues)
- [Changelog](CHANGELOG.md)
- [Structured Warnings Documentation](STRUCTURED_WARNINGS.md)

