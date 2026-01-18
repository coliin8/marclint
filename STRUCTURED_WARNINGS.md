# Structured Warnings

As of version 0.0.2, `marc-lint` provides structured warning objects that can be used for automated processing and API integration. Version 0.0.3 added record identification support.

## Overview

Warnings are represented as `MarcWarning` objects with the following attributes:

- `field`: The MARC field tag (e.g., "020", "245", "LDR" for leader)
- `message`: The error message
- `subfield`: Optional subfield code (e.g., "a", "z")
- `position`: Optional position for repeating fields (0-based index)
- `record_id`: Optional record identifier (from 001 field or explicitly set)

## Usage

### Backward Compatible - String Warnings

The `warnings()` method still returns strings for backward compatibility:

```python
from marc_lint import MarcLint
from pymarc import Record

linter = MarcLint()
linter.check_record(record)

# Returns list of strings
for warning in linter.warnings():
    print(warning)
    # Output: "020: Subfield a has bad checksum"
```

### New - Structured Warnings

Use `warnings_structured()` to get `MarcWarning` objects:

```python
# Returns list of MarcWarning objects
for warning in linter.warnings_structured():
    print(f"Record: {warning.record_id}")
    print(f"Field: {warning.field}")
    print(f"Message: {warning.message}")
    if warning.subfield:
        print(f"Subfield: {warning.subfield}")
    if warning.position is not None:
        print(f"Position: {warning.position}")
```

### Position Tracking for Repeating Fields

When a field appears multiple times in a record, the position is tracked:

```python
# Record with two 020 fields
record = Record()
record.add_field(Field(tag="020", ...))  # Position 0
record.add_field(Field(tag="020", ...))  # Position 1

linter.check_record(record)
for warning in linter.warnings_structured():
    if warning.position is not None:
        print(f"{warning.field}[{warning.position + 1}]: {warning.message}")
        # Output: "020[2]: has bad checksum"
```

### JSON Serialization

Convert warnings to dictionaries for JSON output:

```python
import json

warnings_dict = [w.to_dict() for w in linter.warnings_structured()]
print(json.dumps(warnings_dict, indent=2))
```

Output:
```json
[
  {
    "field": "020",
    "message": "has bad checksum, 123456789X.",
    "subfield": "a",
    "position": 0,
    "record_id": "ocm12345678"
  },
  {
    "field": "245",
    "message": "Must end with . (period).",
    "subfield": null,
    "position": null,
    "record_id": "ocm12345678"
  }
]
```

### String Representation

`MarcWarning` objects can be converted to strings automatically:

```python
warning = MarcWarning(field="020", message="Invalid ISBN", subfield="a", position=1, record_id="ocm12345678")
print(str(warning))
# Output: "Record ocm12345678: 020[2]: Subfield a Invalid ISBN"

warning = MarcWarning(field="245", message="Missing period")
print(str(warning))
# Output: "245: Missing period"
```

Note: When `record_id` is set, it appears as a prefix in the string representation.

## Use Cases

### API Integration

```python
from flask import Flask, jsonify
from marc_lint import MarcLint

app = Flask(__name__)

@app.route('/lint', methods=['POST'])
def lint_marc():
    linter = MarcLint()
    linter.check_record(record)
    
    return jsonify({
        'warnings': [w.to_dict() for w in linter.warnings_structured()]
    })
```

### Filtering by Field

```python
# Get all warnings for field 020
isbn_warnings = [w for w in linter.warnings_structured() if w.field == "020"]

# Get all warnings for a specific subfield
subfield_a_warnings = [w for w in linter.warnings_structured() if w.subfield == "a"]
```

### Grouping by Field

```python
from collections import defaultdict

warnings_by_field = defaultdict(list)
for warning in linter.warnings_structured():
    warnings_by_field[warning.field].append(warning)

for field, warnings in warnings_by_field.items():
    print(f"{field}: {len(warnings)} warnings")
```

### Custom Processing

```python
# Count warnings per field
from collections import Counter

field_counts = Counter(w.field for w in linter.warnings_structured())
print(f"Most problematic field: {field_counts.most_common(1)[0]}")

# Get only subfield-level errors
subfield_errors = [w for w in linter.warnings_structured() if w.subfield]
```

## Batch Processing

Use `check_records()` for processing multiple records with `RecordResult` objects:

```python
from marc_lint import MarcLint
from pymarc import MARCReader

linter = MarcLint()

with open('records.mrc', 'rb') as fh:
    records = list(MARCReader(fh))

results = linter.check_records(records, use_index_as_id=True)

for result in results:
    print(f"Record {result.record_id}: {'Valid' if result.is_valid else 'Invalid'}")
    for warning in result.warnings:
        print(f"  - {warning.field}: {warning.message}")
```

`RecordResult` attributes:
- `record_id`: The record identifier (from 001 field or index)
- `warnings`: List of `MarcWarning` objects for this record
- `is_valid`: Boolean property, `True` if no warnings
- `record`: Optional reference to the original `pymarc.Record`

## CLI Output

The CLI shows record IDs from the 001 field and supports JSON output:

```bash
$ marc-lint myfile.mrc

--- Record ocm12345678 ---
  020[2]: Subfield a has bad checksum, 123456789X.
  245: Must end with . (period).

============================================================
Processed 1 record(s)
Found 2 warning(s) in 1 record(s)
```

JSON output with `--format json`:

```bash
$ marc-lint myfile.mrc --format json
```

```json
[
  {
    "record_id": "ocm12345678",
    "is_valid": false,
    "warnings": [
      {
        "field": "020",
        "message": "has bad checksum, 123456789X.",
        "subfield": "a",
        "position": 1,
        "record_id": "ocm12345678"
      }
    ]
  }
]
```

## See Also

- [README.md](README.md) - Main documentation
- [CHANGELOG.md](CHANGELOG.md) - Version history
