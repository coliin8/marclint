"""Command-line interface for MARC linting."""

import sys
from pathlib import Path

from pymarc import MARCReader

from .linter import MarcLint


def main():
    """Main CLI entry point for marc-lint."""
    if len(sys.argv) < 2:
        print("Usage: marc-lint <file.mrc>")
        print("\nLint a MARC21 file and report validation warnings.")
        sys.exit(1)

    filepath = Path(sys.argv[1])

    if not filepath.exists():
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)

    linter = MarcLint()
    total_records = 0
    total_warnings = 0

    try:
        with open(filepath, "rb") as fh:
            reader = MARCReader(fh)

            for record in reader:
                total_records += 1
                linter.check_record(record)
                warnings = linter.warnings()

                if warnings:
                    print(f"\n--- Record {total_records} ---")
                    for warning in warnings:
                        print(f"  {warning}")
                    total_warnings += len(warnings)

        print(f"\n{'=' * 60}")
        print(f"Processed {total_records} record(s)")
        print(f"Found {total_warnings} warning(s)")

        if total_warnings > 0:
            sys.exit(1)
        else:
            print("\n✓ No validation warnings found!")
            sys.exit(0)

    except Exception as e:
        print(f"Error reading MARC file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
