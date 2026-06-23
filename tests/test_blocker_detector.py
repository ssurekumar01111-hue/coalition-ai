from listeners.blocker_detector import detect_blocker


def test_detect_blocker_volunteers():
    assert detect_blocker("we don't have enough volunteers") == "volunteers"


def test_detect_blocker_donors():
    assert detect_blocker("there's a major funding gap") == "donors"


def test_detect_blocker_grants():
    assert detect_blocker("we need grant opportunities") == "grants"


def test_detect_blocker_none():
    assert detect_blocker("hello everyone") is None
