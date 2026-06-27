import pytest
import agent.impact_tracker as it

def test_load_stats_missing(tmp_path, monkeypatch):
    """Test that load_stats returns defaults when file missing."""
    temp_file = tmp_path / "impact.json"
    monkeypatch.setattr(it, "IMPACT_FILE", temp_file)
    
    # If the file is missing, it should return default stats
    stats = it.load_stats()
    assert stats == it.DEFAULT_STATS
    # Ensure it's a copy and not the exact same dict object
    assert stats is not it.DEFAULT_STATS

def test_increment_stats(tmp_path, monkeypatch):
    """Test that increment_stats correctly adds values."""
    temp_file = tmp_path / "impact.json"
    monkeypatch.setattr(it, "IMPACT_FILE", temp_file)
    
    # Run increment_stats when file doesn't exist
    updated = it.increment_stats(missions=2, students=100, volunteers=5, grants=1, coalitions=2)
    assert updated["missions_launched"] == 2
    assert updated["students_supported"] == 100
    assert updated["volunteers_mobilized"] == 5
    assert updated["grants_identified"] == 1
    assert updated["coalitions_formed"] == 2

    # Verify that saving works and a successive call adds correctly
    updated2 = it.increment_stats(missions=1, students=50, volunteers=2, grants=0, coalitions=1)
    assert updated2["missions_launched"] == 3
    assert updated2["students_supported"] == 150
    assert updated2["volunteers_mobilized"] == 7
    assert updated2["grants_identified"] == 1
    assert updated2["coalitions_formed"] == 3

def test_stats_persist_load_save(tmp_path, monkeypatch):
    """Test that stats persist across load/save cycles."""
    temp_file = tmp_path / "impact.json"
    monkeypatch.setattr(it, "IMPACT_FILE", temp_file)
    
    custom_stats = {
        "missions_launched": 10,
        "students_supported": 500,
        "volunteers_mobilized": 20,
        "grants_identified": 5,
        "coalitions_formed": 10
    }
    
    it.save_stats(custom_stats)
    
    loaded = it.load_stats()
    assert loaded == custom_stats
