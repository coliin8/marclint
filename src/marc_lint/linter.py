"""Python port of the core behavior of `MARC::Lint`.

This is intended as an educational translation so you can see
what the original Perl code is doing, in a more familiar Python
syntax. It assumes `pymarc` records and fields.

Original MARC::Lint Perl module:
    Copyright (C) 2001-2011 Bryan Baldus, Ed Summers, and Dan Lester
    Available under the Perl License (Artistic + GPL)
    https://metacpan.org/dist/MARC-Lint

Python port:
    Copyright (C) 2025 Jacob Collins
    Available under the MIT License
"""

from __future__ import annotations

from typing import Any, Dict, List, Callable, Optional
import re

from pymarc import Record, Field
from stdnum import isbn as stdnum_isbn
from stdnum import issn as stdnum_issn

from .field_rules import RuleGenerator
from .code_data import (
    GEOG_AREA_CODES,
    OBSOLETE_GEOG_AREA_CODES,
    LANGUAGE_CODES,
    OBSOLETE_LANGUAGE_CODES,
)
from .warning import MarcWarning


class MarcLint:
    """Rough Python equivalent of `MARC::Lint`.

    Main entrypoint is `check_record(record)`, after which you can
    inspect `warnings()` for any messages.
    """

    def __init__(self) -> None:
        self._warnings: list[MarcWarning] = []
        self._rules = RuleGenerator().rules
        self._field_positions: Dict[
            str, int
        ] = {}  # Track positions of repeating fields

    # -------- warning handling --------

    def warnings(self) -> List[str]:
        """Return warnings accumulated by the last `check_record` call as strings.

        For backward compatibility, this returns strings.
        Use warnings_structured() for structured warning objects.
        """
        return [str(w) for w in self._warnings]

    def warnings_structured(self) -> List[MarcWarning]:
        """Return warnings as structured MarcWarning objects."""
        return list(self._warnings)

    def clear_warnings(self) -> None:
        self._warnings = []
        self._field_positions = {}

    def warn(
        self,
        field: str,
        message: str,
        subfield: Optional[str] = None,
        position: Optional[int] = None,
    ) -> None:
        """Add a structured warning.

        Args:
            field: The MARC field tag (e.g., "020", "245")
            message: The error message
            subfield: Optional subfield code (e.g., "a", "z")
            position: Optional position for repeating fields (0-based index)
        """
        self._warnings.append(
            MarcWarning(
                field=field, message=message, subfield=subfield, position=position
            )
        )

    # -------- main record check --------

    def check_record(self, marc: Record) -> None:
        """Run lint checks on a `pymarc.Record`.

        Mirrors the Perl `check_record` method: validates 1XX count,
        presence of 245, field repeatability, indicators, subfields,
        control-field rules, and then any tag-specific `check_xxx`
        method that exists on this class.
        """

        self.clear_warnings()

        if not isinstance(marc, Record):
            self.warn("", "Must pass a MARC::Record-like object to check_record")
            return

        one_xx = [f for f in marc.get_fields() if f.tag.startswith("1")]
        if len(one_xx) > 1:
            self.warn(
                "1XX",
                f"Only one 1XX tag is allowed, but I found {len(one_xx)} of them.",
            )

        if not marc.get_fields("245"):
            self.warn("245", "No 245 tag.")

        field_seen: Dict[str, int] = {}
        rules = self._rules
        for field in marc.get_fields():
            tagno = field.tag

            tagrules: dict[str, Any] | None = None

            # Track field position for this tag
            key = f"880.{tagno}" if tagno == "880" else tagno
            position = field_seen.get(key, 0)
            self._field_positions[tagno] = position

            if tagno == "880":
                sub6 = field.get_subfields("6")
                if not sub6:  # no subfield 6 in 880 field
                    self.warn("880", "No subfield 6.", position=position)
                    field_seen[key] = position + 1
                    continue
                # Check the referenced field
                tagno = sub6[0][:3]
                tagrules = rules.get(tagno)
                if not tagrules:
                    field_seen[key] = position + 1
                    continue
                if not tagrules.get("repeatable") and position > 0:
                    self.warn(tagno, "Field is not repeatable.", position=position)
            else:
                tagrules = rules.get(tagno)
                if not tagrules:
                    field_seen[key] = position + 1
                    continue
                if not tagrules.get("repeatable") and position > 0:
                    self.warn(tagno, "Field is not repeatable.", position=position)

            try:
                tag_int = int(tagno)
            except ValueError:
                tag_int = 10

            if tag_int >= 10:
                self.check_indicators(tagno, field, tagrules, position)
                self.check_subfields(tagno, field, tagrules, position)
            else:
                # control fields (<010): no subfield delimiters allowed
                if "\x1f" in (field.data or ""):
                    self.warn(
                        tagno,
                        "Subfields are not allowed in fields lower than 010",
                        position=position,
                    )

            # call tag-specific checker method if it exists
            checker_name = f"check_{tagno}"
            checker: Callable[[Field, int], None] | None = getattr(
                self, checker_name, None
            )
            if callable(checker):
                checker(field, position)

            field_seen[key] = position + 1

    # # -------- General checks --------

    def check_indicators(
        self, tagno: str, field: Field, tagrules: dict[str, Any], position: int = 0
    ) -> None:
        """General indicator checks for any field."""
        # indicator checks (pymarc exposes them via `indicators` list)
        indicator_rules = tagrules.get("indicators", {})
        for ind_index in (1, 2):
            indicator_rule = indicator_rules.get(f"ind{ind_index}")
            # ind_index is 1- or 2-based; convert to 0-based index
            ind_value = " "
            # pymarc represents missing indicators as ' ' (space) or None
            if hasattr(field, "indicators") and len(field.indicators) >= ind_index:
                ind_value = field.indicators[ind_index - 1] or " "
            regex = indicator_rule.get("regex")
            desc = indicator_rule.get("description")
            if regex is None:
                continue
            pattern = re.compile(regex) if isinstance(regex, str) else regex
            if not pattern.match(ind_value):
                self.warn(
                    tagno,
                    f'Indicator {ind_index} must be {desc} but it\'s "{ind_value}"',
                    position=position if position > 0 else None,
                )

    def check_subfields(
        self, tagno: str, field: Field, tagrules: dict[str, Any], position: int = 0
    ) -> None:
        """General subfield checks for any field."""
        subpairs = self._get_subfield_pairs(field)
        # Check subfields against repeat rules
        sub_seen: dict[str, int] = {}
        subfields_rules = tagrules.get("subfields", {})
        for code, data in subpairs:
            rule = subfields_rules.get(code)
            # rule = tagrules.get(code)
            if rule is None:
                self.warn(
                    tagno,
                    f"Subfield _{code} is not allowed.",
                    position=position if position > 0 else None,
                )
            elif not rule.get("repeatable") and sub_seen.get(code):
                self.warn(
                    tagno,
                    f"Subfield _{code} is not repeatable.",
                    position=position if position > 0 else None,
                )

            if any(ch in data for ch in ("\t", "\r", "\n")):
                self.warn(
                    tagno,
                    f"Subfield _{code} has an invalid control character",
                    subfield=code,
                    position=position if position > 0 else None,
                )

            sub_seen[code] = sub_seen.get(code, 0) + 1

    # -------- specific tag checks (subset) --------

    def check_020(self, field: Field, position: int = 0) -> None:
        """Validate ISBNs in 020$a and 020$z.

        Uses python-stdnum library for standard ISBN validation.
        """

        subpairs = self._get_subfield_pairs(field)
        pos = position if position > 0 else None

        for code, data in subpairs:
            # Extract ISBN number (remove hyphens and extract digits/X)
            isbnno = data.replace("-", "")
            m = re.search(r"\D*(\d{9,12}[X\d])\b", isbnno)
            isbnno = m.group(1) if m else ""

            if code == "a":
                if isbnno and not data.startswith(isbnno):
                    self.warn(
                        "020",
                        "may have invalid characters.",
                        subfield="a",
                        position=pos,
                    )

                if "(" in data and not re.search(r"[X0-9] \(", data):
                    self.warn(
                        "020",
                        f"qualifier must be preceded by space, {data}.",
                        subfield="a",
                        position=pos,
                    )

                if not re.match(r"^(?:\d{10}|\d{13}|\d{9}X)$", isbnno):
                    self.warn(
                        "020",
                        f"has the wrong number of digits, {data}.",
                        subfield="a",
                        position=pos,
                    )
                else:
                    # Use python-stdnum for validation
                    if not stdnum_isbn.is_valid(isbnno):
                        if len(isbnno) == 10:
                            self.warn(
                                "020",
                                f"has bad checksum, {data}.",
                                subfield="a",
                                position=pos,
                            )
                        elif len(isbnno) == 13:
                            self.warn(
                                "020",
                                f"has bad checksum (13 digit), {data}.",
                                subfield="a",
                                position=pos,
                            )

            elif code == "z":
                if data.startswith("ISBN") or re.match(r"^\d*-\d+", data):
                    if len(isbnno) == 10 and stdnum_isbn.is_valid(isbnno):
                        self.warn(
                            "020", "is numerically valid.", subfield="z", position=pos
                        )

    def check_022(self, field: Field, position: int = 0) -> None:
        """Validate ISSNs in 022$a, 022$y, and 022$z.

        Uses python-stdnum library for standard ISSN validation.
        - $a: valid ISSN
        - $y: incorrect ISSN (but should be numerically valid)
        - $z: canceled ISSN
        """

        subpairs = self._get_subfield_pairs(field)
        pos = position if position > 0 else None

        for code, data in subpairs:
            # Extract ISSN number (remove hyphens and find 8-digit sequence)
            # ISSN format: 8 characters (7 digits + check digit which can be X)
            m = re.search(r"(\d{4}-?\d{3}[X\d])\b", data, re.I)
            if m:
                issnno = m.group(1).replace("-", "").upper()
            else:
                issnno = ""

            if code == "a":
                # Check if ISSN appears to be at start of subfield
                if issnno and not re.match(r"^\d{4}-?\d{3}[X\d]", data, re.I):
                    self.warn(
                        "022",
                        "may have invalid characters.",
                        subfield="a",
                        position=pos,
                    )

                # Check for proper hyphen format if hyphen is present
                if "-" in data and issnno:
                    # Should be XXXX-XXXX format
                    if not re.match(r"^\d{4}-\d{3}[\dXx]", data, re.I):
                        self.warn(
                            "022",
                            f"has improper hyphen placement, {data}.",
                            subfield="a",
                            position=pos,
                        )

                # Check length
                if not re.match(r"^\d{7}[X\d]$", issnno, re.I):
                    self.warn(
                        "022",
                        f"has the wrong number of digits, {data}.",
                        subfield="a",
                        position=pos,
                    )
                else:
                    # Use python-stdnum for validation
                    if not stdnum_issn.is_valid(issnno):
                        self.warn(
                            "022",
                            f"has bad checksum, {data}.",
                            subfield="a",
                            position=pos,
                        )

            elif code == "y":
                # Incorrect ISSN - warn if it's actually valid
                if issnno and stdnum_issn.is_valid(issnno):
                    self.warn(
                        "022", "is numerically valid.", subfield="y", position=pos
                    )

            elif code == "z":
                # Canceled ISSN - just check format (length)
                if not issnno:
                    self.warn(
                        "022",
                        f"has invalid format, {data}.",
                        subfield="z",
                        position=pos,
                    )
                elif not re.match(r"^\d{7}[X\d]$", issnno, re.I):
                    self.warn(
                        "022",
                        f"has invalid format, {data}.",
                        subfield="z",
                        position=pos,
                    )

    def check_041(self, field: Field, position: int = 0) -> None:
        """Language code validation for 041.

        - If indicator 2 is not '7', each subfield value must have
          length divisible by 3.
        - Each 3-character chunk is validated against language code
          tables from `CodeData.pm`.
        """

        subpairs = self._get_subfield_pairs(field)
        pos = position if position > 0 else None

        ind2 = ""
        if hasattr(field, "indicators") and len(field.indicators) >= 2:
            ind2 = field.indicators[1] or ""

        if ind2 != "7":
            for code, value in subpairs:
                if len(value) % 3 != 0:
                    self.warn(
                        "041",
                        f"must be evenly divisible by 3 or exactly three characters if ind2 is not 7, ({value}).",
                        subfield=code,
                        position=pos,
                    )
                    continue

                codes041: List[str] = [
                    value[pos : pos + 3] for pos in range(0, len(value), 3)
                ]
                for c in codes041:
                    valid = 1 if LANGUAGE_CODES.get(c) else 0
                    obsolete = 1 if OBSOLETE_LANGUAGE_CODES.get(c) else 0
                    if not valid:
                        if obsolete:
                            self.warn(
                                "041",
                                f"{value}, may be obsolete.",
                                subfield=code,
                                position=pos,
                            )
                        else:
                            self.warn(
                                "041",
                                f"{value} ({c}), is not valid.",
                                subfield=code,
                                position=pos,
                            )

    def check_043(self, field: Field, position: int = 0) -> None:
        """Geographic area code validation for 043$a."""

        subpairs = self._get_subfield_pairs(field)
        pos = position if position > 0 else None

        for code, value in subpairs:
            if code != "a":
                continue
            if len(value) != 7:
                self.warn(
                    "043",
                    f"must be exactly 7 characters, {value}",
                    subfield="a",
                    position=pos,
                )
            else:
                valid = 1 if GEOG_AREA_CODES.get(value) else 0
                obsolete = 1 if OBSOLETE_GEOG_AREA_CODES.get(value) else 0
                if not valid:
                    if obsolete:
                        self.warn(
                            "043",
                            f"{value}, may be obsolete.",
                            subfield="a",
                            position=pos,
                        )
                    else:
                        self.warn(
                            "043", f"{value}, is not valid.", subfield="a", position=pos
                        )

    def check_130(self, field: Field, position: int = 0) -> None:
        """Uniform title heading - validate non-filing indicator."""
        self._check_article(field, position)

    def check_240(self, field: Field, position: int = 0) -> None:
        """Uniform title - validate non-filing indicator."""
        self._check_article(field, position)

    def check_245(self, field: Field, position: int = 0) -> None:
        """Port of the complex 245 title checks from Perl.

        This method enforces:
        - presence and position of subfield a (and 6 when present)
        - final punctuation
        - punctuation and spacing around subfields b, c, h, n, p
        - calls `_check_article` for non-filing indicator logic.
        """

        tagno = "245"
        pos = position if position > 0 else None

        # Use safe subfield access; `get_subfields` returns [] if missing
        if not field.get_subfields("a"):
            self.warn("245", "Must have a subfield _a.", position=pos)

        subs = field.subfields
        flat: List[str] = []
        has_sub_6 = False
        # Support flat [code, data, ...] or Subfield objects
        if subs and isinstance(subs[0], str):
            iterable = list(zip(subs[0::2], subs[1::2]))  # type: ignore[arg-type]
        else:
            iterable = []
            for sf in subs:
                code = getattr(sf, "code", None)
                data = getattr(sf, "value", None)
                if code is None or data is None:
                    continue
                iterable.append((code, data))

        # Build flat list in natural order: [code0, data0, code1, data1, ...]
        for code, data in iterable:
            if code == "6":
                has_sub_6 = True
            flat.append(str(code))
            flat.append(str(data))

        # Final punctuation check looks at the last data element
        last_data = flat[-1] if flat else ""
        if isinstance(last_data, str) and not re.search(r"[.?!]$", last_data):
            self.warn("245", "Must end with . (period).", position=pos)
        elif isinstance(last_data, str) and re.search(r"[?!]$", last_data):
            self.warn(
                "245",
                "MARC21 allows ? or ! as final punctuation but LCRI 1.0C, Nov. 2003 (LCPS 1.7.1 for RDA records), requires period.",
                position=pos,
            )

        if has_sub_6:
            if len(flat) < 4:
                self.warn("245", "May have too few subfields.", position=pos)
            else:
                if flat[0] != "6":
                    self.warn(
                        tagno,
                        f"First subfield must be _6, but it is _{flat[0]}",
                        position=pos,
                    )
                if flat[2] != "a":
                    self.warn(
                        tagno,
                        f"First subfield after subfield _6 must be _a, but it is _{flat[2]}",
                        position=pos,
                    )
        else:
            if flat and flat[0] != "a":
                self.warn(
                    tagno,
                    f"First subfield must be _a, but it is _{flat[0]}",
                    position=pos,
                )

        if field.get_subfields("c"):
            for i in range(2, len(flat), 2):
                if flat[i] == "c":
                    if not re.search(r"\s/$", flat[i - 1]):
                        self.warn(
                            "245", "Subfield _c must be preceded by /", position=pos
                        )
                    if re.search(r"\b\w\. \b\w\.", flat[i + 1]) and not re.search(
                        r"\[\bi\.e\. \b\w\..*\]", flat[i + 1]
                    ):
                        self.warn(
                            "245",
                            "Subfield _c initials should not have a space.",
                            position=pos,
                        )
                    break

        if field.get_subfields("b"):
            for i in range(2, len(flat), 2):
                if flat[i] == "b" and not re.search(r" [:;=]$", flat[i - 1]):
                    self.warn(
                        "245",
                        "Subfield _b should be preceded by space-colon, space-semicolon, or space-equals sign.",
                        position=pos,
                    )

        if field.get_subfields("h"):
            for i in range(2, len(flat), 2):
                if flat[i] == "h":
                    if not re.search(r"(\S$)|(\-\- $)", flat[i - 1]):
                        self.warn(
                            "245",
                            "Subfield _h should not be preceded by space.",
                            position=pos,
                        )
                    if not re.match(r"^\[\w*\s*\w*\]", flat[i + 1]):
                        self.warn(
                            "245",
                            f"Subfield _h must have matching square brackets, {flat[i]}.",
                            position=pos,
                        )

        if field.get_subfields("n"):
            for i in range(2, len(flat), 2):
                if flat[i] == "n" and not re.search(r"(\S\.$)|(\-\- \.$)", flat[i - 1]):
                    self.warn(
                        "245",
                        "Subfield _n must be preceded by . (period).",
                        position=pos,
                    )

        if field.get_subfields("p"):
            for i in range(2, len(flat), 2):
                if flat[i] == "p":
                    if flat[i - 2] == "n" and not re.search(
                        r"(\S,$)|(\-\- ,$)", flat[i - 1]
                    ):
                        self.warn(
                            "245",
                            "Subfield _p must be preceded by , (comma) when it follows subfield _n.",
                            position=pos,
                        )
                    elif flat[i - 2] != "n" and not re.search(
                        r"(\S\.$)|(\-\- \.$)", flat[i - 1]
                    ):
                        self.warn(
                            "245",
                            "Subfield _p must be preceded by . (period) when it follows a subfield other than _n.",
                            position=pos,
                        )

        self._check_article(field, position)

    def check_630(self, field: Field, position: int = 0) -> None:
        """Subject added entry-Uniform title - validate non-filing indicator."""
        self._check_article(field, position)

    def check_730(self, field: Field, position: int = 0) -> None:
        """Added entry-Uniform title - validate non-filing indicator."""
        self._check_article(field, position)

    def check_830(self, field: Field, position: int = 0) -> None:
        """Series added entry-Uniform title - validate non-filing indicator."""
        self._check_article(field, position)

    # -------- internal helpers --------

    def _get_subfield_pairs(self, field: Field) -> List[tuple[str, str]]:
        """Extract subfield code/data pairs from a field.

        Supports both flat list format ['a', 'Title', 'b', 'Subtitle']
        and Subfield object format [Subfield('a', 'Title'), Subfield('b', 'Subtitle')].

        Returns:
            List of (code, data) tuples.
        """
        raw_subs = getattr(field, "subfields", [])
        subpairs: List[tuple[str, str]] = []

        if raw_subs and isinstance(raw_subs[0], str):
            # Flat form: [code, data, code, data, ...]
            subpairs = list(zip(raw_subs[0::2], raw_subs[1::2]))  # type: ignore[arg-type]
        else:
            # Object form: [Subfield(code, value), ...]
            for sf in raw_subs:
                code = getattr(sf, "code", None)
                data = getattr(sf, "value", None)
                if code is None or data is None:
                    continue
                subpairs.append((str(code), str(data)))

        return subpairs

    def _check_article(self, field: Field, position: int = 0) -> None:
        """Validate non-filing indicators for article-initial titles.

        Checks whether the non-filing character count indicator correctly
        reflects the presence and length of initial articles in various
        languages. Used for uniform titles and main titles (130, 240, 245,
        630, 730, 830).

        Articles are matched against a curated list of known indefinite/
        definite articles from multiple languages, with exceptions for
        phrases that start with article-like words but shouldn't be treated
        as articles (e.g., "Los Angeles", "A & E").
        """

        # Map article strings to language codes where they function as articles
        # Format: article (lowercase) -> space-separated ISO 639-2 language codes
        ARTICLES = {
            "a": "eng glg hun por",  # English, Galician, Hungarian, Portuguese
            "an": "eng",  # English
            "das": "ger",  # German
            "dem": "ger",  # German
            "der": "ger",  # German
            "ein": "ger",  # German
            "eine": "ger",  # German
            "einem": "ger",  # German
            "einen": "ger",  # German
            "einer": "ger",  # German
            "eines": "ger",  # German
            "el": "spa",  # Spanish
            "en": "cat dan nor swe",  # Catalan, Danish, Norwegian, Swedish
            "gl": "ita",  # Italian
            "gli": "ita",  # Italian
            "il": "ita mlt",  # Italian, Maltese
            "l": "cat fre ita mlt",  # Catalan, French, Italian, Maltese
            "la": "cat fre ita spa",  # Catalan, French, Italian, Spanish
            "las": "spa",  # Spanish
            "le": "fre ita",  # French, Italian
            "les": "cat fre",  # Catalan, French
            "lo": "ita spa",  # Italian, Spanish
            "los": "spa",  # Spanish
            "os": "por",  # Portuguese
            "the": "eng",  # English
            "um": "por",  # Portuguese
            "uma": "por",  # Portuguese
            "un": "cat spa fre ita",  # Catalan, Spanish, French, Italian
            "una": "cat spa ita",  # Catalan, Spanish, Italian
            "une": "fre",  # French
            "uno": "ita",  # Italian
        }

        # Phrases that begin with article-like words but should NOT be
        # treated as having a non-filing article (proper nouns, acronyms, etc.)
        ARTICLE_EXCEPTIONS = {
            "A & E",  # TV channel/brand
            "A & ",  # Generic "A and" pattern
            "A-",  # A-prefix words (A-level, etc.)
            "A+",  # Grade designation
            "A is ",  # "A" as subject
            "A isn't ",  # "A" as subject
            "A l'",  # French "à l'" (not article "a")
            "A la ",  # "À la" French phrase
            "A posteriori",  # Latin phrase
            "A priori",  # Latin phrase
            "A to ",  # "A" as letter/item
            "El Nino",  # Weather phenomenon
            "El Salvador",  # Country name
            "L is ",  # "L" as subject
            "L-",  # L-prefix words
            "La Salle",  # Proper name
            "Las Vegas",  # City name
            "Lo cual",  # Spanish relative pronoun phrase
            "Lo mein",  # Food name
            "Lo que",  # Spanish relative pronoun phrase
            "Los Alamos",  # City name
            "Los Angeles",  # City name
        }

        # Determine which field we're checking (handle 880 linked fields)
        tagno = field.tag
        if tagno == "880" and field["6"]:
            tagno = field["6"][:3]

        # Only validate fields that use non-filing indicators
        if tagno not in {"130", "240", "245", "440", "630", "730", "830"}:
            return

        pos = position if position > 0 else None

        # Different fields use different indicator positions:
        # - 130, 630, 730 use indicator 1 (first)
        # - 240, 245, 830 use indicator 2 (second)
        if tagno in {"130", "630", "730"}:
            ind = ""
            if hasattr(field, "indicators") and len(field.indicators) >= 1:
                ind = field.indicators[0] or ""
            first_or_second = "1st"
        else:
            ind = ""
            if hasattr(field, "indicators") and len(field.indicators) >= 2:
                ind = field.indicators[1] or ""
            first_or_second = "2nd"

        # Indicator must be numeric (0-9)
        if not re.match(r"^[0-9]$", ind):
            self.warn(tagno, "Non-filing indicator is non-numeric", position=pos)

        # Extract title from subfield $a
        sub_a = field.get_subfields("a")
        title = sub_a[0] if sub_a else ""

        # Count and strip leading non-alphanumeric characters
        # (quotes, brackets, parentheses, asterisks)
        char1_notalphanum = 0
        while title and title[0] in "\"'[*":
            char1_notalphanum += 1
            title = title[1:]

        # Extract first word and following separator/text
        # Pattern matches: word + optional separator + rest of string
        m = re.match(r"^([^ \(\)\[\]'\"\-]+)([ \(\)\[\]'\"])?(.*)", title, re.I)
        if m:
            firstword, separator, etc = m.group(1), m.group(2) or "", m.group(3) or ""
        else:
            firstword, separator, etc = "", "", ""

        # Calculate non-filing character count:
        # article length + leading punctuation + trailing space
        nonfilingchars = len(firstword) + char1_notalphanum + 1

        # Check if title starts with an exception phrase (case-insensitive)
        isan_exception = any(
            re.match(rf"^{re.escape(k)}", title, re.I) for k in ARTICLE_EXCEPTIONS
        )

        # Check if first word is an article (and not an exception)
        fw_lower = firstword.lower()
        isan_article = bool(ARTICLES.get(fw_lower) and not isan_exception)

        if isan_article:
            # If there's a separator and following text, count additional
            # leading punctuation characters
            if separator and etc and etc[0] in " ()[]'\"-":
                while etc and etc[0] in " \"'[]()*":
                    nonfilingchars += 1
                    etc = etc[1:]

            # Special case: "en" is ambiguous (could be article or not)
            # Accept either 0 (not treated as article) or 3 (treated as article)
            if fw_lower == "en":
                if ind not in {"3", "0"}:
                    self.warn(
                        tagno,
                        f"First word, , {fw_lower}, may be an article, check {first_or_second} indicator ({ind}).",
                        position=pos,
                    )
            # Standard case: indicator should match calculated non-filing count
            elif str(nonfilingchars) != ind:
                self.warn(
                    tagno,
                    f"First word, {fw_lower}, may be an article, check {first_or_second} indicator ({ind}).",
                    position=pos,
                )
        else:
            # If first word is not an article, indicator should be 0
            if ind != "0":
                self.warn(
                    tagno,
                    f"First word, {fw_lower}, does not appear to be an article, check {first_or_second} indicator ({ind}).",
                    position=pos,
                )
