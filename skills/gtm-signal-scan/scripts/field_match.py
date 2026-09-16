#!/usr/bin/env python3
"""Compare a field value across two sources without failing on cosmetic difference.

Two providers describing the same person rarely spell it the same way. Observed
in one afternoon on one contact: a CRM index held "VP, Go to Market" while the
same provider's people-search returned "VP, Go-to-Market". Elsewhere the same
seat appears as "Co-Founder", "Cofounder" and "Co Founder"; as "Chief Revenue
Officer" and "Chief Revenue Officer (CRO)"; as "SVP Strategy & Commercial" and
"SVP Strategy and Commercial".

None of those are disagreements. A comparison that treats them as disagreements
produces false mismatches, and a false mismatch is worse than no check: it sends
someone to re-source a field that was already correct, or silently drops a real
match from a qualification search.

So: normalize before comparing, and keep the normalizer narrow. It folds
punctuation, spacing, case, and a small fixed set of seniority abbreviations. It
does NOT stem, guess synonyms, or fold distinct functions together -- "Head of
Sales" and "Head of Marketing" must stay different, and the self-tests assert
that, so a normalizer that collapsed everything would fail rather than pass.

Usage:
    python3 field_match.py "<value a>" "<value b>"
    python3 field_match.py --self-test

Exit codes:
    0  the two values agree once normalized
    1  they genuinely differ
    2  usage error
"""

import json
import re
import sys

# Seniority abbreviations only. Expanding beyond this is where a normalizer
# starts inventing equivalences nobody asked for.
ABBREVIATIONS = {
    "vp": "vice president",
    "svp": "senior vice president",
    "evp": "executive vice president",
    "avp": "associate vice president",
    "cro": "chief revenue officer",
    "cmo": "chief marketing officer",
    "ceo": "chief executive officer",
    "coo": "chief operating officer",
    "cto": "chief technology officer",
    "cfo": "chief financial officer",
    "cco": "chief commercial officer",
    "gtm": "go to market",
    "ae": "account executive",
    "sdr": "sales development representative",
    "bdr": "business development representative",
    "revops": "revenue operations",
    "sr": "senior",
    "jr": "junior",
}

# Closed compounds: written with no separator at all, so punctuation folding
# cannot reach them. "Cofounder" is the one that actually occurs; resist adding
# speculative entries, because each one is an equivalence nobody verified.
COMPOUNDS = {
    "cofounder": "co founder",
    "cofounders": "co founders",
    "gotomarket": "go to market",
}

_PARENTHETICAL = re.compile(r"\([^)]*\)")
_STRIP = re.compile(r"[^a-z0-9 ]+")
_SPACES = re.compile(r"\s+")


def normalize(value):
    """Fold cosmetic variation out of a field value.

    Order matters: parentheticals go before punctuation folding, or "(CRO)"
    becomes a bare token and starts matching things it should not.
    """
    if value is None:
        return ""
    text = str(value).lower()
    text = _PARENTHETICAL.sub(" ", text)
    text = text.replace("&", " and ")
    # _STRIP below replaces EVERY non-alphanumeric with a space, hyphens and
    # dashes included. An explicit separator class here was redundant with it:
    # deleting that class left all 20 self-tests passing, which is the
    # definition of a check that cannot fail, so it was removed rather than
    # kept as reassurance.
    text = _STRIP.sub(" ", text)
    tokens = []
    for token in _SPACES.sub(" ", text).strip().split():
        token = COMPOUNDS.get(token, token)
        tokens.extend(ABBREVIATIONS.get(t, t) for t in token.split())
    return " ".join(tokens)


def agree(a, b):
    """True when two values describe the same thing once normalized."""
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        # An absent value is not a disagreement; it is an absence. Callers that
        # care about the difference should check for it before calling.
        return na == nb
    return na == nb


SELF_TESTS = [
    # --- must AGREE: cosmetic difference only -------------------------------
    ("hyphenation", "VP, Go-to-Market", "VP, Go to Market", True),
    ("co-founder spellings", "Co-Founder", "Cofounder", True),
    ("co founder spaced", "Co Founder", "Co-Founder", True),
    ("trailing parenthetical", "Chief Revenue Officer (CRO)", "Chief Revenue Officer", True),
    ("ampersand vs and", "SVP Strategy & Commercial", "SVP Strategy and Commercial", True),
    ("abbreviation expands", "VP Sales", "Vice President Sales", True),
    ("abbreviation both ways", "CRO", "Chief Revenue Officer", True),
    ("comma and case", "head of sales", "Head of Sales,", True),
    ("extra whitespace", "  Head   of  Sales ", "Head of Sales", True),
    ("em dash", "VP—Sales", "VP Sales", True),
    ("gtm expands", "GTM Engineer", "Go to Market Engineer", True),
    ("revops expands", "RevOps Manager", "Revenue Operations Manager", True),
    ("both absent", None, "", True),

    # --- must DIFFER: a normalizer that collapses everything fails here ------
    ("different function", "Head of Sales", "Head of Marketing", False),
    ("different seniority", "VP Sales", "Director Sales", False),
    ("founding IC is not founder", "Founding Account Executive", "Founder", False),
    ("different company function", "Chief Revenue Officer", "Chief Technology Officer", False),
    ("one absent one present", "", "Head of Sales", False),
    ("substring is not a match", "Sales", "Head of Sales", False),
    ("svp is not vp", "SVP Sales", "VP Sales", False),
]


def self_test():
    failures = 0
    for name, a, b, expected in SELF_TESTS:
        got = agree(a, b)
        ok = got == expected
        if not ok:
            failures += 1
        print(("PASS  " if ok else "FAIL  ") + name)
        if not ok:
            print("        " + repr(a) + " vs " + repr(b)
                  + " -> expected " + str(expected) + ", got " + str(got))
            print("        normalized: " + repr(normalize(a)) + " / " + repr(normalize(b)))
    print()
    print(str(len(SELF_TESTS) - failures) + "/" + str(len(SELF_TESTS)) + " passed")
    return failures


def main(argv):
    if len(argv) == 2 and argv[1] == "--self-test":
        return 1 if self_test() else 0
    if len(argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    a, b = argv[1], argv[2]
    result = {
        "a": a, "b": b,
        "normalized_a": normalize(a), "normalized_b": normalize(b),
        "agree": agree(a, b),
    }
    print(json.dumps(result, indent=2))
    return 0 if result["agree"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
