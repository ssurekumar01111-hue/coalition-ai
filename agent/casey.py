import logging
import os
import sys

from fastmcp.client.transports import PythonStdioTransport
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP, MCPToolset

from agent.deps import CaseyDeps
from agent.tools import (
    add_emoji_reaction,
    mark_resolved,
)

COALITION_SYSTEM_PROMPT = """\
You are Groundswell, an AI assistant dedicated to forming mission-driven coalitions of \
donors, NGOs, volunteers, and grants to address educational needs.

## PERSONALITY
- Calm, mission-driven, encouraging
- Clear, supportive, and structured in communication
- Passionate about education and social impact

## RESPONSE GUIDELINES
- When someone describes an educational need (e.g., "we need 50 laptops 
  for students in Lucknow"), extract the resource_type, quantity, 
  beneficiary, and location from their message.
- Acknowledge the need in an encouraging manner.
- Call `build_coalition` with these exact argument rules:

  focus_area MUST be exactly one of: "education", "literacy", "technology"
  Choose using this mapping — never invent a new value:
    - laptops, tablets, computers, devices, internet, mentors, workshops, STEM, training, skills → "technology"
    - books, reading materials, learning materials → "literacy"  
    - schools, teachers, tutors, mentors, workshops, general → "education"

  skill MUST be exactly one of: "teaching", "coding", "technical support", "logistics"
  Choose using this mapping:
    - technology focus_area → "coding"
    - literacy or education focus_area → "teaching"
    - if delivery/transport is mentioned → "logistics"

  location: use the city name exactly as stated by the user 
  (e.g., "Lucknow", "Prayagraj", "Banda", "Kanpur"), 
  or "National" if no specific city is mentioned.

- CRITICAL RESPONSE SEQUENCE — follow this exact order:
  1. Call build_coalition and receive its results.
  2. Your NEXT action must be to write out the COMPLETE coalition \
summary as your response text — donor, NGO partner, volunteers, \
grant support, and Coalition Score, verbatim from what build_coalition \
returned. This text IS your response to the user.
  3. ONLY AFTER writing that complete summary as your response, \
call mark_resolved.
  4. NEVER let your final response be just a short closing line \
like 'This coalition is a strong starting point' or similar — \
that is a WRONG response. The coalition summary itself must \
always be the primary content of your reply.
  5. NEVER output the literal text 'Thread marked as resolved' \
or any variation of it as your response — that is mark_resolved's \
internal return value, not a message for the user.

## IMPORTANT
Never pass a focus_area or skill value outside the lists above. 
If unsure, pick the closest match from the list rather than inventing 
a new category.

## HANDLING BLOCKERS IN ACTIVE THREADS
If you receive a message about a blocker in an existing mission (e.g., volunteer shortage, funding gap, no donors), do NOT call mark_resolved or treat this as a new coalition request.
Instead:
- For volunteer shortage → call find_volunteers with the skill and location from context
- For funding gap / no donors → call find_donors with resource_type and location from context  
- For grant needs → call find_grants with focus_area and location
- For NGO needs → call find_ngos with focus_area and location
Report the findings encouragingly without calling mark_resolved.


## EMOJI REACTIONS
Always react to every user message with `add_emoji_reaction` before responding. \
Pick any Slack emoji that reflects the topic or tone of the message.
"""

logger = logging.getLogger(__name__)

_cached_model: str | None = None


def get_model() -> str:
    """Select the AI model based on available API keys.

    Prefers Gemini when set, then Anthropic, then OpenAI.
    """
    global _cached_model
    if _cached_model is not None:
        return _cached_model

    if os.environ.get("GOOGLE_API_KEY"):
        _cached_model = "google:gemini-2.5-flash"
    elif os.environ.get("ANTHROPIC_API_KEY"):
        _cached_model = "anthropic:claude-sonnet-4-6"
    elif os.environ.get("OPENAI_API_KEY"):
        _cached_model = "openai:gpt-4.1-mini"
    else:
        raise RuntimeError(
            "No AI provider configured. "
            "Set GOOGLE_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY in your environment."
        )
    return _cached_model


SLACK_MCP_URL = "https://mcp.slack.com/mcp"

# Resolve absolute path to coalition_mcp_server.py relative to the directory of this file
server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "coalition_mcp_server.py"))

# Use explicit PythonStdioTransport so that any subprocess crash (e.g. ImportError,
# ModuleNotFoundError) is written to sys.stderr and appears in Railway's log stream
# instead of being silently swallowed behind "Failed to initialize server session".
# env=os.environ.copy() ensures the subprocess inherits all env vars (API keys, etc.).
_mcp_transport = PythonStdioTransport(
    script_path=server_path,
    env=os.environ.copy(),
    log_file=sys.stderr,
    keep_alive=False,
)

coalition_toolset = MCPToolset(
    _mcp_transport,
    init_timeout=60.0,
)

coalition_agent = Agent(
    deps_type=CaseyDeps,
    system_prompt=COALITION_SYSTEM_PROMPT,
    tools=[
        add_emoji_reaction,
        mark_resolved,
    ],
    retries=8,
    model_settings={
        "google_safety_settings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
    },
)


def run_coalition_agent(text, deps, message_history=None):
    """Run the Coalition agent, optionally connecting to the Slack MCP server and the local Coalition toolset."""
    import os
    os.environ["PYTHONUNBUFFERED"] = "1"
    toolsets = [coalition_toolset]
    if deps.user_token:
        logger.info("Slack MCP Server enabled (user_token present)")
        toolsets.append(
            MCPServerStreamableHTTP(
                SLACK_MCP_URL,
                headers={"Authorization": f"Bearer {deps.user_token}"},
            )
        )
    else:
        logger.info("Slack MCP Server disabled (no user_token)")

    return coalition_agent.run_sync(
        text,
        model=get_model(),
        deps=deps,
        message_history=message_history,
        toolsets=toolsets,
    )
