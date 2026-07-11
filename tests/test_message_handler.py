import logging
from unittest.mock import Mock

from slack_bolt import BoltContext, Say, SayStream, SetStatus
from slack_sdk import WebClient

from listeners.events.message import handle_message

test_logger = logging.getLogger(__name__)


class TestMessageHandler:
    def setup_method(self):
        self.fake_client = Mock(WebClient)
        self.fake_context = Mock(BoltContext)
        self.fake_context.bot_user_id = "U_BOT"
        self.fake_say = Mock(Say)
        self.fake_say_stream = Mock(SayStream)
        self.fake_set_status = Mock(SetStatus)

    def test_ignores_bot_mentions_in_threads(self):
        event = {
            "channel": "C123",
            "thread_ts": "123.456",
            "ts": "123.789",
            "text": "<@U_BOT> we need books",
            "channel_type": "channel"
        }

        # If the bot is mentioned, handle_message should return immediately and not call any reactions or slack APIs.
        handle_message(
            client=self.fake_client,
            context=self.fake_context,
            event=event,
            logger=test_logger,
            say=self.fake_say,
            say_stream=self.fake_say_stream,
            set_status=self.fake_set_status,
        )

        self.fake_client.reactions_add.assert_not_called()
