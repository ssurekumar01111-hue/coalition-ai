import re
import logging

logger = logging.getLogger(__name__)


def _build_canvas_content(resource_type: str, location: str,
                          coalition_result: str) -> str:
    """Build structured markdown content for the mission Canvas."""
    from datetime import date
    today = date.today().strftime("%B %d, %Y")
    
    return f"""# 🚀 Mission: {resource_type.title()} for {location}

## 📋 Mission Overview
- **Resource Needed:** {resource_type.title()}
- **Location:** {location}, Uttar Pradesh
- **Launch Date:** {today}
- **Status:** 🟡 Active

## 🤝 Coalition Summary
{coalition_result}

## ✅ Next Steps
- [ ] Contact donor to confirm resource availability
- [ ] Coordinate with NGO partner on delivery logistics
- [ ] Brief volunteers on mission objectives
- [ ] Submit grant application if deadline is within 30 days
- [ ] Schedule kickoff call with all stakeholders

## 📊 Progress Tracking
| Milestone | Status | Owner |
|-----------|--------|-------|
| Coalition formed | ✅ Done | Coalition AI |
| Donor confirmed | ⏳ Pending | Mission Lead |
| NGO briefed | ⏳ Pending | Mission Lead |
| Volunteers onboarded | ⏳ Pending | Volunteer Coord |
| Resources delivered | ⏳ Pending | All |

## 📝 Updates
_Post mission updates here as the coalition progresses._
"""


def create_mission_channel(client, coalition_result: str, 
                           location: str, resource_type: str,
                           team_id: str) -> str | None:
    """Creates a Slack mission channel and posts coalition summary.
    Returns channel_id if created, None if failed or already exists."""
    
    clean_resource = re.sub(r'[^a-z0-9-]', '',
                            resource_type.lower().replace(' ', '-'))
    clean_location = re.sub(r'[^a-z0-9-]', '',
                            location.lower().replace(' ', '-'))
    channel_name = f"mission-{clean_resource}-{clean_location}"[:80]

    try:
        response = client.conversations_create(
            name=channel_name,
            is_private=False,
            team_id=team_id
        )
        channel_id = response["channel"]["id"]

        client.chat_postMessage(
            channel=channel_id,
            text=(
                f"🚀 *Mission Launched: {resource_type.title()} for "
                f"{location}*\n\n"
                f"{coalition_result}\n\n"
                f"_This mission channel was automatically created by "
                f"Coalition AI._"
            )
        )

        # Create a structured Canvas in the mission channel
        try:
            canvas_content = _build_canvas_content(
                resource_type, location, coalition_result
            )
            client.canvases_create(
                channel_id=channel_id,
                document_content={
                    "type": "markdown",
                    "markdown": canvas_content
                }
            )
        except Exception as e:
            logger.warning(f"Canvas creation failed: {e}")

        return channel_id

    except Exception as e:
        logger.warning(f"Mission channel creation failed (may already "
                      f"exist): {e}")
        return None
