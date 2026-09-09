from __future__ import annotations

import re

from .intake import normalize_text

POLICY_VERSION = "screening-v2-recall-first"

EXECUTIVE_PATTERNS = (
    r"\bvice president\b", r"\bvp\b", r"\bsvp\b", r"\bevp\b",
    r"\bsenior director\b", r"\bsr\.? director\b", r"\bdirector\b",
    r"\bhead of\b", r"\bglobal head\b", r"\bchief\b",
    r"\bceo\b", r"\bcoo\b", r"\bcio\b", r"\bcto\b", r"\bcdo\b", r"\bcdao\b", r"\bcaio\b",
    r"\bmanaging director\b", r"\bexecutive director\b", r"\bgeneral manager\b",
    r"\bpresident\b", r"\bpartner\b",
)

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
    normalized = normalize_text(title)
    if any(re.search(pattern, normalized) for pattern in CLEAR_NON_TARGET_PATTERNS):
        return "TRIAGE_CLEAR_NO", "HIDDEN", "CLEAR_NON_TARGET_TITLE", 0.99
    if any(re.search(pattern, normalized) for pattern in EXECUTIVE_PATTERNS):
        return "ELIGIBLE", "HIDDEN", "EXECUTIVE_SCOPE_PLAUSIBLE", 0.94
    # Do not reject on missing title altitude alone. Unconventional titles can hide
    # enterprise-scale mandates; CP3 determines relevance from the actual mandate.
    return "ELIGIBLE", "HIDDEN", "MANDATE_REVIEW_REQUIRED", 0.55
