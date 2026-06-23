from listeners.views.app_home_builder import CATEGORIES, build_app_home_view
from listeners.views.feedback_builder import build_feedback_blocks
from listeners.views.issue_modal_builder import build_issue_modal


def test_build_issue_modal():
    category = "We need laptops and devices for students"
    modal = build_issue_modal(category)

    assert modal["type"] == "modal"
    assert modal["callback_id"] == "issue_submission"
    assert modal["title"]["text"] == "🚀 Start a Mission"
    assert modal["private_metadata"] == category

    block_ids = [b.get("block_id") for b in modal["blocks"] if "block_id" in b]
    assert "description_block" in block_ids
    assert "location_block" in block_ids



def test_build_feedback_blocks():
    blocks = build_feedback_blocks()

    assert len(blocks) > 0
    # The block should contain a feedback action
    block_dict = blocks[0].to_dict()
    action_ids = [e["action_id"] for e in block_dict["elements"]]
    assert "feedback" in action_ids


def test_build_app_home_view_default():
    """Shows connected status with hardcoded green Coalition MCP Server connection text."""
    view = build_app_home_view()

    assert view["type"] == "home"

    # Find the actions block containing category buttons
    actions_block = next(b for b in view["blocks"] if b["type"] == "actions")
    assert len(actions_block["elements"]) == len(CATEGORIES)

    # Shows MCP status as connected
    section_texts = [
        b["text"]["text"] for b in view["blocks"] if b["type"] == "section"
    ]
    mcp_section = next(t for t in section_texts if "Coalition MCP Server is connected." in t)
    assert "🟢" in mcp_section


def test_build_app_home_view_with_bot_user_id():
    """bot_user_id provided — context block includes dynamic mention."""
    view = build_app_home_view(bot_user_id="U0BOT")

    context_blocks = [b for b in view["blocks"] if b["type"] == "context"]
    mention_text = context_blocks[0]["elements"][0]["text"]
    assert "<@U0BOT>" in mention_text


def test_build_app_home_view_without_bot_user_id():
    """bot_user_id not provided — context block omits mention."""
    view = build_app_home_view()

    context_blocks = [b for b in view["blocks"] if b["type"] == "context"]
    mention_text = context_blocks[0]["elements"][0]["text"]
    assert "<@" not in mention_text
