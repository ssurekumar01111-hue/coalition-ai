BLOCKER_PATTERNS = {
    "volunteers": [
        "not enough volunteers",
        "need more volunteers",
        "volunteer shortage",
        "no volunteers",
        "lacking volunteers",
        "don't have enough volunteers",
        "do not have enough volunteers",
    ],
    "donors": [
        "funding gap",
        "no donors",
        "need donors",
        "lack of funding",
        "no funding",
        "insufficient funds",
    ],
    "grants": [
        "need grants",
        "no grants",
        "grant shortage",
        "looking for grants",
        "grant opportunities",
    ],
    "ngos": [
        "need ngo",
        "no ngo partner",
        "ngo shortage",
        "need partner",
        "no partner",
    ],
}


def detect_blocker(text: str) -> str | None:
    if not text:
        return None
    lower_text = text.lower()
    for blocker_type, keywords in BLOCKER_PATTERNS.items():
        for keyword in keywords:
            if keyword in lower_text:
                return blocker_type
    return None


def blocker_to_tool_call(blocker_type: str, context_text: str) -> dict:
    mapping = {
        "volunteers": {
            "tool": "find_volunteers",
            "message": "🚨 Volunteer shortage detected! Let me find available volunteers...",
        },
        "donors": {
            "tool": "find_donors",
            "message": "🚨 Funding gap detected! Let me search for donors...",
        },
        "grants": {
            "tool": "find_grants",
            "message": "🚨 Grant opportunity needed! Let me search for relevant grants...",
        },
        "ngos": {
            "tool": "find_ngos",
            "message": "🚨 NGO partner needed! Let me find matching organizations...",
        },
    }
    return mapping.get(blocker_type, {})
