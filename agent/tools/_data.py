import os
import json

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))

def load_json(filename: str):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def get_proximity_score(loc1: str, loc2: str) -> int:
    if not loc1 or not loc2:
        return 30
    loc1 = loc1.strip().lower()
    loc2 = loc2.strip().lower()
    if loc1 == loc2:
        return 100
    
    # Uttar Pradesh state/region cities
    up_cities = {"lucknow", "prayagraj", "banda", "kanpur"}
    if loc1 in up_cities and loc2 in up_cities:
        return 60
        
    return 30

def get_donors(resource_type: str, location: str = None):
    donors = load_json("donors.json")
    matched = []
    for d in donors:
        offered = [r.lower() for r in d.get("resources_offered", [])]
        if resource_type.lower() in offered:
            matched.append(d)
    
    if not matched and location:
        for d in donors:
            d["type"] = "General Support"
            d["is_fallback"] = True
        matched = donors
    
    if location:
        matched.sort(key=lambda d: (get_proximity_score(d.get("location"), location), d.get("capacity", 0)), reverse=True)
    else:
        matched.sort(key=lambda d: d.get("capacity", 0), reverse=True)
    return matched

def get_ngos(focus_area: str, location: str = None):
    ngos = load_json("ngos.json")
    matched = [n for n in ngos if n.get("focus_area", "").lower() == focus_area.lower()]
    if location:
        matched.sort(key=lambda n: (n.get("verified", False), get_proximity_score(n.get("location"), location)), reverse=True)
    else:
        matched.sort(key=lambda n: n.get("verified", False), reverse=True)
    return matched

def get_volunteers(skill: str, location: str = None):
    volunteers = load_json("volunteers.json")
    matched = [v for v in volunteers if v.get("skill", "").lower() == skill.lower() and v.get("active", False)]
    if location:
        matched.sort(key=lambda v: get_proximity_score(v.get("location"), location), reverse=True)
    return matched

def get_grants(focus_area: str, location: str = None):
    grants = load_json("grants.json")

    def _match(target_focus_area):
        matched = []
        for g in grants:
            if g.get("focus_area", "").lower() != target_focus_area.lower():
                continue
            if location:
                scope = g.get("location_scope", "")
                if scope.lower() not in [location.lower(), "national"]:
                    continue
            matched.append(g)
        matched.sort(key=lambda g: g.get("deadline", "9999-12-31"))
        return matched

    # Try exact match first
    results = _match(focus_area)

    # Fallback: if no exact match and focus_area isn't already
    # "education", retry with "education" as a general catch-all
    # (every grant in this domain ultimately funds education)
    if not results and focus_area.lower() != "education":
        results = _match("education")

    return results
