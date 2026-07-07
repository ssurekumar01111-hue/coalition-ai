def build_issue_modal(category: str) -> dict:
    """Build the mission submission modal pre-filled with selected need type."""

    # Map category values to example placeholder text
    placeholders = {
        "We need laptops and devices for students": (
            "e.g. We need 50 laptops for 200 students in Lucknow by August 2026"
        ),
        "We need books and reading materials for children": (
            "e.g. We need books and reading materials for 300 children in Banda"
        ),
        "We need STEM workshop mentors for students": (
            "e.g. We need STEM workshop mentors for 100 students in Kanpur"
        ),
        "We need mentors and tutors for underserved students": (
            "e.g. We need 10 mentors for underserved students in Prayagraj"
        ),
        "We have an educational need to discuss": (
            "e.g. Describe your educational need and location..."
        ),
    }

    placeholder_text = placeholders.get(
        category, "Describe your educational need..."
    )

    return {
        "type": "modal",
        "callback_id": "issue_submission",
        "title": {"type": "plain_text", "text": "🚀 Start a Mission"},
        "submit": {"type": "plain_text", "text": "Launch Mission"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "private_metadata": category,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Need type:* {category}\n\n"
                        "Describe your need in detail — Groundswell will "
                        "assemble donors, NGOs, volunteers, and grants "
                        "around it."
                    ),
                },
            },
            {
                "type": "input",
                "block_id": "description_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "description_input",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": placeholder_text,
                    },
                },
                "label": {"type": "plain_text", "text": "Describe your need"},
            },
            {
                "type": "input",
                "block_id": "location_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "location_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "e.g. Lucknow, Banda, Kanpur, Prayagraj",
                    },
                },
                "label": {"type": "plain_text", "text": "Location"},
            },
        ],
    }
