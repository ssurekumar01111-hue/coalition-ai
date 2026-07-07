"""Tests for listeners/utils/mission_channel.py"""
import pytest
from unittest.mock import MagicMock, call
from slack_sdk.errors import SlackApiError

from listeners.utils.mission_channel import create_mission_channel


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_client(create_side_effect=None, list_channels=None):
    """Return a mock Slack WebClient with sensible defaults."""
    client = MagicMock()

    if create_side_effect is not None:
        client.conversations_create.side_effect = create_side_effect
    else:
        client.conversations_create.return_value = {
            "channel": {"id": "C_NEW123"}
        }

    list_channels = list_channels or []
    client.conversations_list.return_value = {"channels": list_channels}

    client.chat_postMessage.return_value = {"ok": True}
    client.conversations_canvases_create.return_value = {"ok": True}

    return client


def _name_taken_error(channel_id_in_body=None):
    """Build a SlackApiError that mimics a name_taken response."""
    response_body = {"ok": False, "error": "name_taken"}
    if channel_id_in_body:
        response_body["channel"] = {"id": channel_id_in_body}
    fake_resp = MagicMock()
    fake_resp.get = lambda key, default=None: response_body.get(key, default)
    fake_resp.__getitem__ = lambda self, key: response_body[key]
    return SlackApiError("name_taken", fake_resp)


COMMON_KWARGS = dict(
    coalition_result="Test coalition summary.",
    location="Lucknow",
    resource_type="laptops",
    team_id="T123",
)


# ── happy-path: new channel ───────────────────────────────────────────────────

class TestCreateMissionChannelNewChannel:
    def test_returns_new_channel_id(self):
        client = _make_client()
        result = create_mission_channel(client, **COMMON_KWARGS)
        assert result == "C_NEW123"

    def test_creates_with_correct_name(self):
        client = _make_client()
        create_mission_channel(client, **COMMON_KWARGS)
        client.conversations_create.assert_called_once_with(
            name="mission-laptops-lucknow",
            is_private=False,
            team_id="T123",
        )

    def test_posts_summary_message(self):
        client = _make_client()
        create_mission_channel(client, **COMMON_KWARGS)
        assert client.chat_postMessage.call_count == 1
        post_kwargs = client.chat_postMessage.call_args.kwargs
        assert post_kwargs["channel"] == "C_NEW123"
        assert "Laptops" in post_kwargs["text"]
        assert "Lucknow" in post_kwargs["text"]

    def test_creates_canvas(self):
        client = _make_client()
        create_mission_channel(client, **COMMON_KWARGS)
        client.conversations_canvases_create.assert_called_once()
        args = client.conversations_canvases_create.call_args.kwargs
        assert args["channel_id"] == "C_NEW123"


# ── name_taken: ID in error body ──────────────────────────────────────────────

class TestNameTakenWithIdInErrorBody:
    def test_returns_existing_id_from_error_body(self):
        err = _name_taken_error(channel_id_in_body="C_EXISTING")
        client = _make_client(create_side_effect=err)

        result = create_mission_channel(client, **COMMON_KWARGS)

        assert result == "C_EXISTING"

    def test_does_not_call_conversations_list_when_id_in_body(self):
        err = _name_taken_error(channel_id_in_body="C_EXISTING")
        client = _make_client(create_side_effect=err)

        create_mission_channel(client, **COMMON_KWARGS)

        client.conversations_list.assert_not_called()

    def test_still_posts_summary_message_on_existing_channel(self):
        err = _name_taken_error(channel_id_in_body="C_EXISTING")
        client = _make_client(create_side_effect=err)

        create_mission_channel(client, **COMMON_KWARGS)

        client.chat_postMessage.assert_called_once()
        assert client.chat_postMessage.call_args.kwargs["channel"] == "C_EXISTING"

    def test_still_creates_canvas_on_existing_channel(self):
        err = _name_taken_error(channel_id_in_body="C_EXISTING")
        client = _make_client(create_side_effect=err)

        create_mission_channel(client, **COMMON_KWARGS)

        client.conversations_canvases_create.assert_called_once()
        args = client.conversations_canvases_create.call_args.kwargs
        assert args["channel_id"] == "C_EXISTING"


# ── name_taken: no ID in body → fallback to conversations_list ───────────────

class TestNameTakenFallbackToList:
    def test_returns_id_from_conversations_list(self):
        err = _name_taken_error()  # no channel in body
        list_channels = [
            {"name": "mission-laptops-lucknow", "id": "C_LIST123"},
            {"name": "general", "id": "C_GEN"},
        ]
        client = _make_client(create_side_effect=err,
                              list_channels=list_channels)

        result = create_mission_channel(client, **COMMON_KWARGS)

        assert result == "C_LIST123"

    def test_calls_conversations_list_with_correct_params(self):
        err = _name_taken_error()
        client = _make_client(
            create_side_effect=err,
            list_channels=[{"name": "mission-laptops-lucknow", "id": "C_LIST123"}],
        )

        create_mission_channel(client, **COMMON_KWARGS)

        client.conversations_list.assert_called_once_with(
            types="public_channel",
            exclude_archived=False,
            limit=1000,
            team_id="T123",
        )

    def test_posts_message_when_id_found_via_list(self):
        err = _name_taken_error()
        client = _make_client(
            create_side_effect=err,
            list_channels=[{"name": "mission-laptops-lucknow", "id": "C_LIST123"}],
        )

        create_mission_channel(client, **COMMON_KWARGS)

        client.chat_postMessage.assert_called_once()
        assert client.chat_postMessage.call_args.kwargs["channel"] == "C_LIST123"

    def test_returns_none_when_not_found_in_list(self):
        err = _name_taken_error()
        client = _make_client(create_side_effect=err, list_channels=[])

        result = create_mission_channel(client, **COMMON_KWARGS)

        assert result is None

    def test_does_not_post_when_id_unresolvable(self):
        err = _name_taken_error()
        client = _make_client(create_side_effect=err, list_channels=[])

        create_mission_channel(client, **COMMON_KWARGS)

        client.chat_postMessage.assert_not_called()


# ── other SlackApiError is re-raised → outer handler returns None ─────────────

class _DictResponse(dict):
    """dict subclass that also exposes .get() so SlackApiError stores it
    in .response and the production code can call e.response.get(...)."""
    pass


class TestOtherSlackApiError:
    def _other_slack_error(self, error_code: str) -> SlackApiError:
        resp = _DictResponse({"ok": False, "error": error_code})
        return SlackApiError(error_code, resp)

    def test_returns_none_on_unknown_slack_error(self):
        client = _make_client(
            create_side_effect=self._other_slack_error("not_in_channel")
        )
        result = create_mission_channel(client, **COMMON_KWARGS)
        assert result is None

    def test_does_not_post_on_unknown_slack_error(self):
        client = _make_client(
            create_side_effect=self._other_slack_error("not_in_channel")
        )
        create_mission_channel(client, **COMMON_KWARGS)
        client.chat_postMessage.assert_not_called()


# ── canvas failure is non-fatal ───────────────────────────────────────────────

class TestCanvasFailure:
    def test_still_returns_channel_id_when_canvas_fails(self):
        client = _make_client()
        client.conversations_canvases_create.side_effect = Exception("canvas_err")

        result = create_mission_channel(client, **COMMON_KWARGS)

        assert result == "C_NEW123"
        client.chat_postMessage.assert_called_once()


# ── channel name sanitisation ─────────────────────────────────────────────────

class TestChannelNameSanitisation:
    def test_spaces_and_caps_removed(self):
        client = _make_client()
        create_mission_channel(
            client,
            coalition_result="x",
            location="New Delhi",
            resource_type="STEM Workshop",
            team_id="T1",
        )
        called_name = client.conversations_create.call_args.kwargs["name"]
        assert called_name == "mission-stem-workshop-new-delhi"

    def test_name_truncated_to_80_chars(self):
        client = _make_client()
        long_location = "a" * 80
        create_mission_channel(
            client,
            coalition_result="x",
            location=long_location,
            resource_type="books",
            team_id="T1",
        )
        called_name = client.conversations_create.call_args.kwargs["name"]
        assert len(called_name) <= 80
