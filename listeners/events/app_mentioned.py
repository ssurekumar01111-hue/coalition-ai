import re
from logging import Logger

from slack_bolt import BoltContext, Say, SayStream, SetStatus
from slack_sdk import WebClient

from agent import CaseyDeps, run_coalition_agent
from thread_context import conversation_store
from listeners.views.feedback_builder import build_feedback_blocks
from listeners.utils.mission_channel import create_mission_channel
from agent.impact_tracker import increment_stats


def handle_app_mentioned(
    client: WebClient,
    context: BoltContext,
    event: dict,
    logger: Logger,
    say: Say,
    say_stream: SayStream,
    set_status: SetStatus,
):
    """Handle @Casey mentions in channels."""
    try:
        channel_id = context.channel_id
        text = event.get("text", "")
        thread_ts = event.get("thread_ts") or event["ts"]
        user_id = context.user_id

        # Strip the bot mention from the text
        cleaned_text = re.sub(r"<@[A-Z0-9]+>", "", text).strip()

        if not cleaned_text:
            say(
                text=(
                    "Hey there! 👋 I'm Coalition AI. Describe an educational need "
                    "(e.g. 'we need 50 laptops for students in Lucknow') and I'll "
                    "autonomously assemble a coalition of donors, NGOs, volunteers, "
                    "and grants to address it."
                ),
                thread_ts=thread_ts,
            )
            return

        # Add eyes reaction only to the first message (not threaded replies)
        if not event.get("thread_ts"):
            client.reactions_add(
                channel=channel_id,
                timestamp=event["ts"],
                name="eyes",
            )

        # Set assistant thread status with loading messages
        set_status(
            status="Thinking...",
            loading_messages=[
                "Teaching the hamsters to type faster…",
                "Untangling the internet cables…",
                "Consulting the office goldfish…",
                "Polishing up the response just for you…",
                "Convincing the AI to stop overthinking…",
            ],
        )

        # Get conversation history
        history = conversation_store.get_history(channel_id, thread_ts)

        # Run the agent
        deps = CaseyDeps(
            client=client,
            user_id=user_id,
            channel_id=channel_id,
            thread_ts=thread_ts,
            message_ts=event["ts"],
            user_token=context.user_token,
        )
        result = run_coalition_agent(cleaned_text, deps, message_history=history)

        # Stream response in thread with feedback buttons
        streamer = say_stream()
        streamer.append(markdown_text=result.output)
        feedback_blocks = build_feedback_blocks()
        streamer.stop(blocks=feedback_blocks)

        # Store conversation history
        conversation_store.set_history(channel_id, thread_ts, result.all_messages())

        # Mission channel auto-creation
        # Only create for top-level mentions (not thread replies)
        if not event.get("thread_ts"):
            try:
                # Extract location from message
                known_cities = ["Lucknow", "Prayagraj", "Banda", "Kanpur"]
                location = "Lucknow"
                for city in known_cities:
                    if city.lower() in cleaned_text.lower():
                        location = city
                        break

                # Extract resource_type from message
                tech_keywords = ["laptop", "tablet", "computer", 
                                "internet", "mentor", "workshop", 
                                "stem", "coding"]
                literacy_keywords = ["book", "reading", "literacy"]
                text_lower = cleaned_text.lower()
                if any(k in text_lower for k in tech_keywords):
                    resource_type = "laptops"
                    if "mentor" in text_lower or "workshop" in text_lower:
                        resource_type = "stem-workshop"
                elif any(k in text_lower for k in literacy_keywords):
                    resource_type = "books"
                else:
                    resource_type = "education"

                mission_channel_id = create_mission_channel(
                    client=client,
                    coalition_result=result.output,
                    location=location,
                    resource_type=resource_type,
                    team_id=event.get("team", "")
                )

                if mission_channel_id:
                    say(
                        text=(
                            f"📌 Mission channel created: "
                            f"<#{mission_channel_id}> — all updates "
                            f"will be coordinated there."
                        ),
                        thread_ts=thread_ts,
                    )
            except Exception as mission_err:
                logger.warning(f"Mission channel creation failed: "
                              f"{mission_err}")

        # Update impact stats
        try:
            # Extract student count from message if mentioned
            count_match = re.search(r'\b(\d+)\b', cleaned_text)
            student_count = int(count_match.group(1)) if count_match else 50
            
            # Extract volunteer count from coalition result
            vol_match = re.search(r'Found (\d+) active volunteer', 
                                  result.output)
            vol_count = int(vol_match.group(1)) if vol_match else 1
            
            # Check if grant was found
            grant_count = 1 if 'Grant Support' in result.output and \
                         'no' not in result.output.lower()[:200] else 0
            
            increment_stats(
                missions=1,
                students=student_count,
                volunteers=vol_count,
                grants=grant_count,
                coalitions=1
            )
        except Exception:
            pass  # Never block the main flow

    except Exception as e:
        logger.exception(f"Failed to handle app mention: {e}")
        say(
            text=f":warning: Something went wrong! ({e})",
            thread_ts=event.get("thread_ts") or event["ts"],
        )
