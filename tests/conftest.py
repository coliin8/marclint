from pytest import fixture
from pymarc import Record, Field, Subfield

from marc_lint.linter import MarcLint


@fixture
def linter():
    """Fresh MarcLint instance for each test."""
    return MarcLint()


def create_minimal_record(fields: list[Field] | None = None) -> Record:
    """Create a minimal valid MARC record with required fields.

    Creates a record with:
    - Valid leader
    - 001 field (control number)
    - 008 field (fixed-length data)
    - 245 field (title)

    Args:
        fields: Optional list of additional fields to add

    Returns:
        A pymarc.Record with the minimal required fields
    """
    rec = Record()
    rec.leader = "00000nam a2200000 i 4500"
    rec.add_field(Field(tag="001", data="test001"))
    rec.add_field(Field(tag="008", data="240101s2024    xxu           000 0 eng d"))
    rec.add_field(
        Field(
            tag="245",
            indicators=["0", "0"],
            subfields=[Subfield("a", "Test title.")],
        )
    )
    if fields:
        for f in fields:
            # Skip 245 if already added and user provides their own
            if f.tag == "245":
                # Remove the default 245 and add the user's
                for existing in rec.get_fields("245"):
                    rec.remove_field(existing)
            rec.add_field(f)
    return rec
