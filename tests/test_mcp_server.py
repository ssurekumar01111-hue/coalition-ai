import pytest
from coalition_mcp_server import (
    find_donors,
    find_ngos,
    find_volunteers,
    find_grants,
    build_coalition,
)

class TestMcpServerTools:
    def test_find_donors(self):
        result = find_donors("laptops", "Lucknow")
        assert "Lucknow Tech Foundation" in result
        assert "Capacity: 100" in result
        assert "Location: Lucknow" in result

    def test_find_donors_no_match(self):
        result = find_donors("nonexistent_resource")
        assert "No donors found" in result

    def test_find_ngos(self):
        result = find_ngos("education", "Lucknow")
        assert "Uttar Pradesh Education Initiative" in result
        assert "Verified ✅" in result

    def test_find_volunteers(self):
        result = find_volunteers("teaching", "Lucknow")
        # Amit Sharma has teaching skill, active=true, location=Lucknow
        assert "Amit Sharma" in result
        assert "Found 3 active volunteer(s)" in result

    def test_find_grants(self):
        result = find_grants("education", "Lucknow")
        assert "UP State Education Fund" in result

    def test_build_coalition(self):
        result = build_coalition("laptops", "education", "Lucknow")
        assert "Recommended Coalition" in result
        assert "Lucknow Tech Foundation" in result
        assert "Uttar Pradesh Education Initiative" in result
        assert "Coalition Score" in result

    def test_kanpur_stem_mentors_coalition(self):
        # Kanpur STEM Foundation offers "mentors"
        result = build_coalition("mentors", "technology", "Kanpur")
        assert "Recommended Coalition" in result
        assert "Kanpur STEM Foundation" in result
        # Kanpur Skill Development Grant has technology focus_area and location_scope Kanpur
        assert "Kanpur Skill Development Grant" in result
        assert "Coalition Score" in result

    def test_non_matching_resource_fallback(self):
        # Nonexistent resource should trigger fallback to proximity-matched donor (General Support)
        result = build_coalition("some_nonexistent_resource", "education", "Lucknow")
        assert "Recommended Coalition" in result
        assert "Lucknow Tech Foundation" in result
        assert "General Support" in result
        assert "Coalition Score" in result

