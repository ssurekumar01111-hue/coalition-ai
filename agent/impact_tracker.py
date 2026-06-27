import json
import pathlib

IMPACT_FILE = pathlib.Path(__file__).parent.parent / "data" / "impact.json"

DEFAULT_STATS = {
    "missions_launched": 0,
    "students_supported": 0,
    "volunteers_mobilized": 0,
    "grants_identified": 0,
    "coalitions_formed": 0
}

def load_stats() -> dict:
    """Load impact stats from file, return defaults if file missing."""
    try:
        if IMPACT_FILE.exists():
            return json.loads(IMPACT_FILE.read_text())
        return DEFAULT_STATS.copy()
    except Exception:
        return DEFAULT_STATS.copy()

def save_stats(stats: dict) -> None:
    """Save impact stats to file."""
    try:
        IMPACT_FILE.parent.mkdir(parents=True, exist_ok=True)
        IMPACT_FILE.write_text(json.dumps(stats, indent=2))
    except Exception:
        pass

def increment_stats(missions: int = 0, students: int = 0,
                   volunteers: int = 0, grants: int = 0,
                   coalitions: int = 0) -> dict:
    """Increment impact stats and save. Returns updated stats."""
    stats = load_stats()
    stats["missions_launched"] += missions
    stats["students_supported"] += students
    stats["volunteers_mobilized"] += volunteers
    stats["grants_identified"] += grants
    stats["coalitions_formed"] += coalitions
    save_stats(stats)
    return stats
