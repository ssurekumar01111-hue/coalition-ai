from logging import Logger

from slack_bolt import Ack
from slack_sdk import WebClient

from agent import CaseyDeps, run_coalition_agent
from listeners.views.feedback_builder import build_feedback_blocks

GENERAL_CHANNEL_ID = "C0BBZPN96PK"


def handle_issue_submission(
    ack: Ack,
    body: dict,
    client: WebClient,
    logger: Logger,
):
    """Handle modal submission: execute the agent directly and post the result."""
    ack()
    try:
        description = body["view"]["state"]["values"]["description_block"][
            "description_input"
        ]["value"]
        location = body["view"]["state"]["values"]["location_block"][
            "location_input"
        ]["value"]
        user_id = body["user"]["id"]

        # Build the need message (avoid duplicating location)
        full_message = f"{description} in {location}"

        # Post the need to #general for visibility
        client.chat_postMessage(
            channel=GENERAL_CHANNEL_ID,
            text=(
                f"📋 *New mission submitted via App Home*\n"
                f"<@{user_id}>: {full_message}"
            ),
        )

        # Post a "thinking" indicator
        thinking = client.chat_postMessage(
            channel=GENERAL_CHANNEL_ID,
            text="👀 Coalition AI is assembling your coalition...",
            thread_ts=None,
        )
        thread_ts = thinking["ts"]

        # Run the coalition agent directly
        deps = CaseyDeps(
            client=client,
            user_id=user_id,
            channel_id=GENERAL_CHANNEL_ID,
            thread_ts=thread_ts,
            message_ts=thread_ts,
            user_token=None,
        )

        logger.info(
            f"Modal submission - running agent with message: {full_message}"
        )
        result = run_coalition_agent(full_message, deps, message_history=None)

        # Post result to #general as a thread reply
        client.chat_postMessage(
            channel=GENERAL_CHANNEL_ID,
            text=result.output,
            thread_ts=thread_ts,
        )

    except Exception as e:
        logger.exception(f"Failed to handle issue submission: {e}")
        client.chat_postMessage(
            channel=GENERAL_CHANNEL_ID,
            text=(
                f":warning: Something went wrong processing your mission request. "
                f"({e})"
            ),
        )
