from __future__ import annotations

import re

POLICY_VERSION = "screening-v3-residual-ambiguity"

EXECUTIVE_MARKERS = (
    r"\bvice president\b", r"\bvp\b", r"\bsvp\b", r"\bevp\b",
    r"\bsenior director\b", r"\bsr director\b", r"\bdirector\b",
    r"\bhead\b", r"\bchief\b", r"\bpresident\b", r"\bpartner\b",
)

# These titles carry enough inherent enterprise authority to remain ambiguous even
# when the function is not visible in the title. Other honorifics (notably bank VP)
# must also carry a target-mandate signal; title altitude alone is not evidence.
INHERENT_AUTHORITY_PATTERNS = (
    r"\bchief\b", r"\bceo\b", r"\bcoo\b", r"\bcio\b", r"\bcto\b",
    r"\bcdo\b", r"\bcdao\b", r"\bcaio\b", r"\bgeneral manager\b",
    r"\bmanaging director\b", r"\bglobal head\b", r"\bhead of\b",
    r"\bexecutive director\b", r"\bsvp\b", r"\bevp\b",
)

# Derived conservatively from the already-paid historical corpus. Each phrase either
# retained a known RELEVANT/POSSIBLE role or represents the same mandate family. The
# rule deliberately routes uncertainty to Sol; it never manufactures a positive
# business outcome.
TARGET_MANDATE_PATTERNS = (
    r"\btransformation\b", r"\bdigital strategy\b", r"\bproduct\b",
    r"\bportfolio lead\b", r"\boperations\b", r"\bautomation\b",
    r"\benterprise platform", r"\bai (?:and )?software engineering\b",
    r"\bapplied ai\b", r"\bclient engagement\b", r"\bdata product\b",
    r"\bdigital assets\b", r"\brevenue operations\b", r"\bnetwork strategy\b",
    r"\bpartnerships operations\b", r"\bapplication engineer", r"\bapplication engineering\b",
    r"\binfrastructure engineering\b", r"\bdata science engineering\b",
    r"\benterprise architect\b", r"\btechnology relationship\b",
    r"\bstrategy and\b", r"\bgovernance\b", r"\bdata management\b",
    r"\bdevops\b", r"\bimplementation consultant\b",
    r"\breliability engineering\b", r"\bengineering team\b",
)

UNCONVENTIONAL_MANDATE_PATTERNS = (r"\bclient partner\b", r"\bsenior product manager\b")


def _normalize_title(value: str) -> str:
    value = (value or "").lower().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()

# Only high-confidence title exclusions belong here. Anything merely uncertain is retained
# below the glass for mandate-aware triage. False positives cost compute; false negatives
# can erase an opportunity before the candidate ever sees it.
CLEAR_NON_TARGET_PATTERNS = (
    r"\bsales development representative\b",
    r"\bbusiness development representative\b",
    r"\badministrative assistant\b",
    r"\bexecutive assistant\b",
    r"\bintern(ship)?\b",
    r"\bcashier\b",
    r"\bwarehouse (associate|worker)\b",
)


def deterministic_screen(title: str) -> tuple[str, str, str, float]:
    normalized = _normalize_title(title)
    if any(re.search(pattern, normalized) for pattern in CLEAR_NON_TARGET_PATTERNS):
        return "TRIAGE_CLEAR_NO", "HIDDEN", "CLEAR_NON_TARGET_TITLE", 0.99
    if any(re.search(pattern, normalized) for pattern in INHERENT_AUTHORITY_PATTERNS):
        return "ELIGIBLE", "HIDDEN", "RESIDUAL_EXECUTIVE_AMBIGUITY", 0.72
    has_altitude = any(re.search(pattern, normalized) for pattern in EXECUTIVE_MARKERS)
    has_target_mandate = any(re.search(pattern, normalized) for pattern in TARGET_MANDATE_PATTERNS)
    if (has_altitude and has_target_mandate) or any(
        re.search(pattern, normalized) for pattern in UNCONVENTIONAL_MANDATE_PATTERNS
    ):
        return "ELIGIBLE", "HIDDEN", "RESIDUAL_MANDATE_AMBIGUITY", 0.68
    if has_altitude:
        return "TRIAGE_CLEAR_NO", "HIDDEN", "TITLE_INFLATED_SPECIALIST", 0.97
    return "TRIAGE_CLEAR_NO", "HIDDEN", "BELOW_EXECUTIVE_MANDATE", 0.98
