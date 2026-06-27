from agent.impact_tracker import load_stats

CATEGORIES = [
    {
        "action_id": "category_laptops_devices",
        "text": ":computer: Laptops & Devices",
        "value": "We need laptops and devices for students",
    },
    {
        "action_id": "category_books_literacy",
        "text": ":books: Books & Literacy",
        "value": "We need books and reading materials for children",
    },
    {
        "action_id": "category_stem_workshops",
        "text": ":microscope: STEM Workshops",
        "value": "We need STEM workshop mentors for students",
    },
    {
        "action_id": "category_mentorship",
        "text": ":mortar_board: Mentorship Programs",
        "value": "We need mentors and tutors for underserved students",
    },
    {
        "action_id": "category_something_else",
        "text": ":speech_balloon: Other Need",
        "value": "We have an educational need to discuss",
    },
]


def build_app_home_view(
    bot_user_id: str | None = None,
) -> dict:
    """Build the App Home Block Kit view with category buttons.

    Args:
        bot_user_id: The bot's user ID for dynamic mentions.
    """
    mention = f" with <@{bot_user_id}>" if bot_user_id else ""
    stats = load_stats()
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "👋 Welcome to Coalition AI",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "I autonomously assemble *donors, NGOs, volunteers, and grants* "
                    "around educational needs — forming mission-driven coalitions in minutes.\n\n"
                    "*Choose a need type below to start a mission*, or mention me in any "
                    "channel with your educational need."
                ),
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*📊 Impact so far:*\n"
                    f"🚀 *{stats['missions_launched']}* missions launched  "
                    f"•  👥 *{stats['students_supported']}* students supported  "
                    f"•  🙋 *{stats['volunteers_mobilized']}* volunteers mobilized  "
                    f"•  💰 *{stats['grants_identified']}* grants identified"
                )
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": cat["text"],
                        "emoji": True,
                    },
                    "action_id": cat["action_id"],
                    "value": cat["value"],
                }
                for cat in CATEGORIES
            ],
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"You can also mention me in any channel{mention} or send me a DM — just describe your educational need and I'll build a coalition.",
                }
            ],
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "⚡ *Powered by:* Slack AI  •  MCP Server  •  Real-Time Search",
                }
            ],
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🟢 *Coalition MCP Server is connected.*",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Querying donors, NGOs, volunteers, and grants in real time.",
                }
            ],
        },
    ]

    return {
        "type": "home",
        "blocks": blocks,
    }
