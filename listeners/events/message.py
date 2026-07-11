from logging import Logger

from slack_bolt import BoltContext, Say, SayStream, SetStatus
from slack_sdk import WebClient

from agent import CaseyDeps, run_coalition_agent
from thread_context import conversation_store
from listeners.views.feedback_builder import build_feedback_blocks
from listeners.blocker_detector import detect_blocker, blocker_to_tool_call


def handle_message(
    client: WebClient,
    context: BoltContext,
    event: dict,
    logger: Logger,
    say: Say,
    say_stream: SayStream,
    set_status: SetStatus,
):
    """Handle messages sent to Casey via DM or in threads the bot is part of."""
    # Issue submissions are posted by the bot with metadata so the message
    # handler can run the agent on behalf of the original user.
    is_issue_submission = (
        event.get("metadata", {}).get("event_type") == "issue_submission"
    )

    # Skip message subtypes (edits, deletes, etc.) and bot messages that
    # are not issue submissions.
    if event.get("subtype"):
        return
    if event.get("bot_id") and not is_issue_submission:
        return

    # Skip if the bot itself is mentioned in the message text.
    # App mention events in threads are handled by app_mentioned.py instead,
    # to avoid concurrent execution and collision on the shared MCP transport.
    if context.bot_user_id and f"<@{context.bot_user_id}>" in event.get("text", ""):
        return

    is_dm = event.get("channel_type") == "im"
    is_thread_reply = event.get("thread_ts") is not None

    if is_dm:
        pass
    elif is_thread_reply:
        # RTS: Check for blockers FIRST, before history guard
        # This enables proactive detection in ANY active mission thread
        # even if the bot was invoked via @mention (not DM/assistant flow)
        blocker = detect_blocker(event.get("text", ""))
        if blocker:
            message_text = event.get("text", "")
            thread_ts = event.get("thread_ts")
            channel_id = event.get("channel")
            
            try:
                # Get thread context to extract location and focus_area
                # Use client.conversations_replies to fetch the thread
                replies = client.conversations_replies(
                    channel=channel_id,
                    ts=thread_ts,
                    limit=10
                )
                thread_texts = " ".join(
                    m.get("text", "") 
                    for m in replies.get("messages", [])
                )
                
                # Extract location from thread context
                known_cities = ["Lucknow", "Prayagraj", "Banda", "Kanpur"]
                location = "Lucknow"  # default
                for city in known_cities:
                    if city.lower() in thread_texts.lower():
                        location = city
                        break
                
                # Extract focus_area from thread context
                tech_keywords = ["laptop", "tablet", "computer", "internet", 
                                "mentor", "workshop", "stem", "coding", "technology"]
                literacy_keywords = ["book", "reading", "literacy", "literature"]
                focus_area = "education"  # default
                thread_lower = thread_texts.lower()
                if any(k in thread_lower for k in tech_keywords):
                    focus_area = "technology"
                elif any(k in thread_lower for k in literacy_keywords):
                    focus_area = "literacy"
                
                # Get tool suggestion
                tool_suggestion = blocker_to_tool_call(blocker, message_text)
                
                # Post immediate alert to thread
                say(
                    text=tool_suggestion["message"],
                    thread_ts=thread_ts
                )
                
                skill_map = {
                    "technology": "coding",
                    "literacy": "teaching", 
                    "education": "teaching"
                }
                skill = skill_map.get(focus_area, "teaching")
                
                tool_name = tool_suggestion["tool"]
                if tool_name == "find_volunteers":
                    tool_args_str = f"skill='{skill}' and location='{location}'"
                elif tool_name == "find_donors":
                    tool_args_str = f"resource_type='{focus_area}' and location='{location}'"
                elif tool_name == "find_grants":
                    tool_args_str = f"focus_area='{focus_area}' and location='{location}'"
                elif tool_name == "find_ngos":
                    tool_args_str = f"focus_area='{focus_area}' and location='{location}'"
                else:
                    tool_args_str = f"location='{location}'"
                
                # Synthesize agent call to resolve the blocker
                synthesized_message = (
                    f"A blocker was detected in this mission thread: '{message_text}'. "
                    f"Location context: {location}. Focus area: {focus_area}. "
                    f"Please call {tool_name} with {tool_args_str} "
                    f"to find resources and resolve this blocker. "
                    f"Report the findings back to the team in an encouraging way."
                )
                
                # Set assistant thread status with loading messages
                set_status(
                    status="Thinking...",
                    loading_messages=[
                        "Teaching the hamsters to type faster…",
                        "Untangling the internet cables…",
                        "Consulting the office goldfish…",
                        "Warming up the coalition engine…",
                        "Polishing up the response just for you…",
                        "Convincing the AI to stop overthinking…",
                    ],
                )
                
                deps = CaseyDeps(
                    client=client,
                    user_id=context.user_id or event.get("user") or "unknown_user",
                    channel_id=channel_id,
                    thread_ts=thread_ts,
                    message_ts=event["ts"],
                    user_token=context.user_token,
                )
                
                thread_history = conversation_store.get_history(channel_id, thread_ts)
                import time
                MAX_MCP_RETRIES = 1
                result = None
                last_error = None
                for attempt in range(MAX_MCP_RETRIES + 1):
                    try:
                        result = run_coalition_agent(synthesized_message, deps, message_history=thread_history)
                        break  # success, exit retry loop
                    except Exception as e:
                        last_error = e
                        error_str = str(e)
                        if "Failed to initialize server session" in error_str or \
                           "Client failed to connect" in error_str:
                            if attempt < MAX_MCP_RETRIES:
                                logger.warning(
                                    f"MCP connection failed (attempt {attempt + 1}/"
                                    f"{MAX_MCP_RETRIES + 1}), retrying silently: {e}"
                                )
                                time.sleep(2)  # brief pause before retry
                                continue
                        raise  # re-raise if not an MCP error, or retries exhausted
                
                if result is None:
                    raise last_error
                
                # Stream response in thread with feedback buttons
                streamer = say_stream()
                streamer.append(markdown_text=result.output)
                feedback_blocks = build_feedback_blocks()
                streamer.stop(blocks=feedback_blocks)
                
                # Store conversation history
                conversation_store.set_history(channel_id, thread_ts, result.all_messages())
            except Exception as e:
                logger.exception(f"Failed to handle blocker message: {e}")
                say(
                    text=f":warning: Something went wrong! ({e})",
                    thread_ts=thread_ts,
                )
            return
        
        # Non-blocker thread reply: use existing history guard
        channel_id = context.channel_id or event.get("channel")
        thread_ts = event.get("thread_ts")
        history = conversation_store.get_history(channel_id, thread_ts)
        if history is None:
            return
    else:
        # Top-level channel messages are handled by app_mentioned
        return

    try:
        channel_id = context.channel_id
        text = event.get("text", "")
        thread_ts = event.get("thread_ts") or event["ts"]

        # For issue submissions the bot posted the message, so the real
        # user_id comes from the metadata rather than the event context.
        if is_issue_submission:
            user_id = event["metadata"]["event_payload"]["user_id"]
        else:
            user_id = context.user_id

        # Get conversation history
        history = conversation_store.get_history(channel_id, thread_ts)

        # Add eyes reaction only to the first message (DMs only — channel
        # threads already have the reaction from the initial app_mention)
        if is_dm and history is None:
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
                "Warming up the coalition engine…",
                "Polishing up the response just for you…",
                "Convincing the AI to stop overthinking…",
            ],
        )

        # Run the agent
        deps = CaseyDeps(
            client=client,
            user_id=user_id,
            channel_id=channel_id,
            thread_ts=thread_ts,
            message_ts=event["ts"],
            user_token=context.user_token,
        )



        import time
        MAX_MCP_RETRIES = 1
        result = None
        last_error = None
        for attempt in range(MAX_MCP_RETRIES + 1):
            try:
                result = run_coalition_agent(text, deps, message_history=history)
                break  # success, exit retry loop
            except Exception as e:
                last_error = e
                error_str = str(e)
                if "Failed to initialize server session" in error_str or \
                   "Client failed to connect" in error_str:
                    if attempt < MAX_MCP_RETRIES:
                        logger.warning(
                            f"MCP connection failed (attempt {attempt + 1}/"
                            f"{MAX_MCP_RETRIES + 1}), retrying silently: {e}"
                        )
                        time.sleep(2)  # brief pause before retry
                        continue
                raise  # re-raise if not an MCP error, or retries exhausted
        
        if result is None:
            raise last_error

        # Stream response in thread with feedback buttons
        streamer = say_stream()
        streamer.append(markdown_text=result.output)
        feedback_blocks = build_feedback_blocks()
        streamer.stop(blocks=feedback_blocks)

        # Store conversation history
        conversation_store.set_history(channel_id, thread_ts, result.all_messages())

    except Exception as e:
        logger.exception(f"Failed to handle message: {e}")
        say(
            text=f":warning: Something went wrong! ({e})",
            thread_ts=event.get("thread_ts") or event.get("ts"),
        )
