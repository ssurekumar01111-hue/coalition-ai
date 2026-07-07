import os
import pathlib
from google import genai
from google.genai import types
from mcp.server.fastmcp import FastMCP
from datetime import datetime
from agent.tools._data import (
    get_donors,
    get_ngos,
    get_volunteers,
    get_grants,
    get_proximity_score,
)
import sys
import logging
# Redirect all logging to stderr so stdout stays clean for MCP protocol
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

mcp = FastMCP("coalition-ai-tools")

def get_deadline_urgency_score(deadline_str: str) -> int:
    try:
        deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d")
        current_date = datetime(2026, 6, 20)
        days = (deadline_date - current_date).days
        if days <= 0:
            return 20
        elif days <= 15:
            return 50
        elif days <= 30:
            return 80
        else:
            return 100
    except Exception:
        return 70

def generate_ai_grants(focus_area: str, location: str) -> list:
    """Use Gemini to generate contextually relevant Indian government 
    education scheme suggestions when seeded data is insufficient."""
    try:
        client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY", ""))
        
        prompt = f"""You are an expert on Indian government education schemes and grants.

Generate 2 real or realistic Indian government education funding schemes 
or grants relevant for:
- Focus area: {focus_area}
- Location: {location}, Uttar Pradesh, India

Return ONLY a JSON array with exactly 2 objects, each with these fields:
- name: string (official or realistic scheme name)
- focus_area: string (must be exactly "{focus_area}")
- location_scope: string (either "{location}" or "Uttar Pradesh" or "National")
- deadline: string (future date YYYY-MM-DD within 6 months from 2026-06-25)
- amount_range: string (e.g. "50000-200000")
- source: string (ministry or department name)

Base on real schemes: PM eVidya, Samagra Shiksha, NMMS, AICTE schemes, 
UP government education initiatives, etc.
Return ONLY the JSON array, no other text, no markdown fences."""

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        
        import json
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()
        
        schemes = json.loads(text)
        return schemes if isinstance(schemes, list) else []
    except Exception:
        return []


@mcp.tool()
def find_donors(resource_type: str, location: str = None) -> str:
    """Find donors matching a specific resource type.

    Use this tool to find potential donors who offer resources matching the requested type,
    optionally sorting or filtering them by proximity to the target location.

    Args:
        resource_type: The type of resource needed (e.g., 'laptops', 'tablets', 'books').
        location: Optional location of the need (e.g., 'Lucknow').
    """
    donors = get_donors(resource_type, location)
    if not donors:
        return f"No donors found offering '{resource_type}'."
    
    matches = donors[:5]
    if any(d.get("is_fallback") for d in donors):
        lines = [f"No donors found offering '{resource_type}'. Showing general support donors matching location:"]
    else:
        lines = [f"Found {len(donors)} donor(s) offering '{resource_type}':"]
    for d in matches:
        offered_str = ", ".join(d.get("resources_offered", []))
        lines.append(
            f"- **{d['name']}** ({d['type']}) | Capacity: {d['capacity']} | Location: {d['location']} (Offered: {offered_str})"
        )
    return "\n".join(lines)

@mcp.tool()
def find_ngos(focus_area: str, location: str = None) -> str:
    """Find NGOs matching a specific focus area and location.

    Use this tool to find partner NGOs with a matching focus area (e.g., 'education', 'technology'),
    optionally prioritizing those close to the target location, preferring verified NGOs.

    Args:
        focus_area: The focus area of the NGO (e.g., 'education', 'technology', 'literacy').
        location: Optional location of the need (e.g., 'Lucknow').
    """
    ngos = get_ngos(focus_area, location)
    if not ngos:
        return f"No NGOs found with focus area '{focus_area}'."
    
    matches = ngos[:3]
    lines = [f"Found {len(ngos)} NGO(s) specializing in '{focus_area}':"]
    for n in matches:
        verified_str = "Verified ✅" if n.get("verified", False) else "Unverified"
        lines.append(
            f"- **{n['name']}** | Location: {n['location']} | Status: {verified_str}"
        )
    return "\n".join(lines)

@mcp.tool()
def find_volunteers(skill: str, location: str = None) -> str:
    """Find active volunteers matching a specific skill.

    Use this tool to find active volunteers with the specified skill, optionally sorting by
    proximity to a target location.

    Args:
        skill: The skill required (e.g., 'teaching', 'coding', 'technical support').
        location: Optional location of the need (e.g., 'Lucknow').
    """
    volunteers = get_volunteers(skill, location)
    if not volunteers:
        return f"No active volunteers found with skill '{skill}'."
    
    matches = volunteers[:5]
    lines = [f"Found {len(volunteers)} active volunteer(s) with skill '{skill}':"]
    for v in matches:
        lines.append(
            f"- **{v['name']}** | Skill: {v['skill']} | Location: {v['location']}"
        )
    return "\n".join(lines)

@mcp.tool()
def find_grants(focus_area: str, location: str = None) -> str:
    """Find grants and government schemes matching a focus area and location.
    
    Uses curated local grant data enhanced with AI-powered discovery of 
    relevant Indian government education schemes via Gemini.

    Args:
        focus_area: The focus area of the grant (e.g., 'education', 
                    'technology', 'literacy').
        location: Optional location of the need (e.g., 'Lucknow').
    """
    # Get seeded grants first
    seeded_grants = get_grants(focus_area, location)
    
    # If we have 2+ seeded matches, use them directly
    if len(seeded_grants) >= 2:
        matches = seeded_grants[:3]
        lines = [f"Found {len(seeded_grants)} grant(s) for '{focus_area}':"]
        for g in matches:
            lines.append(
                f"- **{g['name']}** | Scope: {g['location_scope']} "
                f"| Deadline: {g['deadline']}"
            )
        return "\n".join(lines)
    
    # Otherwise enhance with AI-generated schemes
    ai_grants = generate_ai_grants(focus_area, location or "Uttar Pradesh")
    
    all_grants = seeded_grants.copy()
    for ag in ai_grants:
        ag["_ai_generated"] = True
        all_grants.append(ag)
    
    if not all_grants:
        return f"No grants found for focus area '{focus_area}'."
    
    lines = [f"Found {len(all_grants)} grant(s) for '{focus_area}' "
             f"(including AI-discovered government schemes):"]
    for g in all_grants[:3]:
        source_tag = " 🤖" if g.get("_ai_generated") else ""
        scope = g.get("location_scope", "N/A")
        deadline = g.get("deadline", "N/A")
        lines.append(
            f"- **{g['name']}**{source_tag} | Scope: {scope} "
            f"| Deadline: {deadline}"
        )
    if any(g.get("_ai_generated") for g in all_grants[:3]):
        lines.append(
            "_🤖 AI-discovered schemes based on Indian government "
            "education programs_"
        )
    return "\n".join(lines)

@mcp.tool()
def build_coalition(resource_type: str, focus_area: str, location: str) -> str:
    """Build a recommended coalition for educational resource needs.

    Use this signature tool to assemble donors, NGOs, active volunteers, and grants matching the
    location and resource requirements. It computes a weighted Coalition Score out of 100.

    Args:
        resource_type: The type of resource requested (e.g., 'laptops', 'tablets', 'books').
        focus_area: The focus area for NGOs/grants (e.g., 'education', 'technology', 'literacy').
        location: The location of the educational need (e.g., 'Lucknow').
    """
    donors = get_donors(resource_type, location)
    ngos = get_ngos(focus_area, location)
    
    skill = "teaching"
    focus_lower = focus_area.lower()
    if "tech" in focus_lower or "code" in focus_lower:
        skill = "coding"
    elif "support" in focus_lower or "system" in focus_lower:
        skill = "technical support"
    elif "logistics" in focus_lower or "dist" in focus_lower:
        skill = "logistics"
        
    volunteers = get_volunteers(skill, location)
    grants = get_grants(focus_area, location)
    if not grants:
        ai_grants = generate_ai_grants(focus_area, location)
        grants = ai_grants  # use AI grants as fallback

    selected_donor = donors[0] if donors else None
    selected_ngo = ngos[0] if ngos else None
    selected_grant = grants[0] if grants else None
    vol_count = len(volunteers)

    d_prox = get_proximity_score(selected_donor.get("location") if selected_donor else None, location)
    n_prox = get_proximity_score(selected_ngo.get("location") if selected_ngo else None, location)
    proximity_score = (d_prox + n_prox) / 2
    
    if selected_donor:
        cap = selected_donor.get("capacity", 0)
        if cap >= 100:
            capacity_score = 100
        elif cap >= 50:
            capacity_score = 85
        elif cap >= 25:
            capacity_score = 65
        else:
            capacity_score = 45
    else:
        capacity_score = 0

    if selected_ngo:
        alignment_score = 100 if selected_ngo.get("verified", False) else 80
    else:
        alignment_score = 0

    vol_sub = min(100, vol_count * 20)
    if selected_grant:
        grant_sub = get_deadline_urgency_score(selected_grant.get("deadline", ""))
    else:
        grant_sub = 40
    availability_score = (vol_sub * 0.5) + (grant_sub * 0.5)

    final_score = int(
        (proximity_score * 0.3) +
        (capacity_score * 0.25) +
        (alignment_score * 0.25) +
        (availability_score * 0.2)
    )

    lines = [
        f"### 🤝 Recommended Coalition for {location} ({resource_type.capitalize()} Need)",
        ""
    ]
    
    if selected_donor:
        lines.append(f"- **Donor**: {selected_donor['name']} ({selected_donor['type']}) | Capacity: {selected_donor['capacity']} | Location: {selected_donor['location']}")
    else:
        lines.append("- **Donor**: None matching found")
        
    if selected_ngo:
        verified_tag = "Verified ✅" if selected_ngo.get("verified", False) else "Unverified"
        lines.append(f"- **NGO Partner**: {selected_ngo['name']} | Location: {selected_ngo['location']} | Status: {verified_tag}")
    else:
        lines.append("- **NGO Partner**: None matching found")

    lines.append(f"- **Volunteers**: Found {vol_count} active volunteer(s) with skill '{skill}'")
    
    if selected_grant:
        lines.append(f"- **Grant Support**: {selected_grant['name']} | Deadline: {selected_grant['deadline']} | Scope: {selected_grant['location_scope']}")
    else:
        lines.append("- **Grant Support**: None matching found")

    lines.append("")
    lines.append(f"**Coalition Score**: {final_score}/100")
    lines.append(
        f"- _Proximity (30%)_: {int(proximity_score)} | "
        f"_Capacity (25%)_: {int(capacity_score)} | "
        f"_Alignment (25%)_: {int(alignment_score)} | "
        f"_Availability (20%)_: {int(availability_score)}"
    )
    
    return "\n".join(lines)

if __name__ == "__main__":
    # DEBUG: surface data directory resolution into Railway logs via stderr.
    # Remove once the data-file path issue is confirmed resolved.
    import sys as _sys
    _data_dir = pathlib.Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "data")))
    print(f"DEBUG: DATA_DIR resolved to: {_data_dir}", file=_sys.stderr, flush=True)
    print(f"DEBUG: DATA_DIR exists: {_data_dir.exists()}", file=_sys.stderr, flush=True)
    print(f"DEBUG: Files in DATA_DIR: {list(_data_dir.glob('*.json')) if _data_dir.exists() else 'N/A'}", file=_sys.stderr, flush=True)
    mcp.run()
