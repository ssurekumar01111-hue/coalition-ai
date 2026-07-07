import re
import logging
from slack_sdk.errors import SlackApiError

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
| Coalition formed | ✅ Done | Groundswell |
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
    Returns channel_id if created or already exists, None if failed."""
    
    clean_resource = re.sub(r'[^a-z0-9-]', '',
                            resource_type.lower().replace(' ', '-'))
    clean_location = re.sub(r'[^a-z0-9-]', '',
                            location.lower().replace(' ', '-'))
    channel_name = f"mission-{clean_resource}-{clean_location}"[:80]

    channel_id = None
    try:
        response = client.conversations_create(
            name=channel_name,
            is_private=False,
            team_id=team_id
        )
        channel_id = response["channel"]["id"]
    except SlackApiError as e:
        if e.response.get("error") == "name_taken":
            # Channel already exists from a prior run — look up its ID.
            # Slack's name_taken error body sometimes includes the existing
            # channel object; try that first before making a list call.
            channel_id = e.response.get("channel", {}).get("id")
            if not channel_id:
                # Fallback: search the first page of public channels.
                # Enterprise Grid workspaces require team_id in conversations.list calls.
                list_kwargs = {
                    "types": "public_channel",
                    "exclude_archived": False,
                    "limit": 1000,
                }
                if team_id:
                    list_kwargs["team_id"] = team_id
                list_resp = client.conversations_list(**list_kwargs)
                matched = [
                    c for c in list_resp.get("channels", [])
                    if c["name"] == channel_name
                ]
                channel_id = matched[0]["id"] if matched else None

            if not channel_id:
                logger.warning(
                    f"Channel #{channel_name} exists but ID could "
                    f"not be resolved"
                )
                return None

            logger.info(f"Reusing existing channel #{channel_name} "
                        f"(id={channel_id})")
        else:
            # Any other Slack error (permissions, rate-limit, etc.) —
            # log it and bail; the outer except handles non-Slack errors.
            logger.warning(f"Mission channel creation failed: {e}")
            return None
    except Exception as e:
        logger.warning(f"Mission channel creation failed: {e}")
        return None

    if channel_id:
        try:
            client.chat_postMessage(
                channel=channel_id,
                text=(
                    f"🚀 *Mission Launched: {resource_type.title()} for "
                    f"{location}*\n\n"
                    f"{coalition_result}\n\n"
                    f"_This mission channel was automatically created by "
                    f"Groundswell._"
                )
            )

            # Create a structured Canvas in the mission channel
            try:
                canvas_content = _build_canvas_content(
                    resource_type, location, coalition_result
                )
                client.conversations_canvases_create(
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
            logger.warning(f"Post/Canvas creation failed: {e}")
            return channel_id

    return None
