import re
import logging

logger = logging.getLogger(__name__)


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
        return channel_id

    except Exception as e:
        logger.warning(f"Mission channel creation failed (may already "
                      f"exist): {e}")
        return None
