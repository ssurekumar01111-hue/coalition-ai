from unittest.mock import Mock, patch
import pytest
from slack_bolt import BoltContext
from slack_sdk import WebClient

from listeners.events.app_mentioned import handle_app_mentioned

class TestMCPRetry:
    def setup_method(self):
        self.fake_client = Mock(WebClient)
        self.fake_context = Mock(BoltContext)
        self.fake_context.user_id = "U123"
        self.fake_context.channel_id = "C123"
        self.fake_context.user_token = "fake-token"
        
        self.fake_event = {
            "text": "<@Casey> we need laptops in Kanpur",
            "ts": "123456.789",
            "team": "T123",
        }
        
        self.fake_logger = Mock()
        self.fake_say = Mock()
        self.fake_say_stream = Mock()
        self.fake_set_status = Mock()
        
        # Stream mock
        self.stream_mock = Mock()
        self.fake_say_stream.return_value = self.stream_mock

    @patch("listeners.events.app_mentioned.run_coalition_agent")
    @patch("time.sleep")
    def test_mcp_retry_success(self, mock_sleep, mock_run_agent):
        mock_result = Mock()
        mock_result.output = "Successful summary."
        mock_result.all_messages.return_value = []
        
        # First call raises MCP session error, second call succeeds
        mock_run_agent.side_effect = [
            Exception("Failed to initialize server session: timeout"),
            mock_result
        ]
        
        handle_app_mentioned(
            client=self.fake_client,
            context=self.fake_context,
            event=self.fake_event,
            logger=self.fake_logger,
            say=self.fake_say,
            say_stream=self.fake_say_stream,
            set_status=self.fake_set_status
        )
        
        assert mock_run_agent.call_count == 2
        mock_sleep.assert_called_once_with(2)
        self.stream_mock.append.assert_called_once_with(markdown_text="Successful summary.")

    @patch("listeners.events.app_mentioned.run_coalition_agent")
    @patch("time.sleep")
    def test_mcp_retry_exhausted(self, mock_sleep, mock_run_agent):
        # Always raises MCP error
        mock_run_agent.side_effect = Exception("Client failed to connect to server")
        
        handle_app_mentioned(
            client=self.fake_client,
            context=self.fake_context,
            event=self.fake_event,
            logger=self.fake_logger,
            say=self.fake_say,
            say_stream=self.fake_say_stream,
            set_status=self.fake_set_status
        )
        
        assert mock_run_agent.call_count == 2  # Attempt 1 + 1 retry
        assert mock_sleep.call_count == 1
        
        # Confirm that the error was caught and posted to the channel
        self.fake_say.assert_called_with(
            text=":warning: Something went wrong! (Client failed to connect to server)",
            thread_ts="123456.789"
        )

    @patch("listeners.events.app_mentioned.run_coalition_agent")
    @patch("time.sleep")
    def test_non_mcp_error_no_retry(self, mock_sleep, mock_run_agent):
        # Raises some other error
        mock_run_agent.side_effect = ValueError("Some other error")
        
        handle_app_mentioned(
            client=self.fake_client,
            context=self.fake_context,
            event=self.fake_event,
            logger=self.fake_logger,
            say=self.fake_say,
            say_stream=self.fake_say_stream,
            set_status=self.fake_set_status
        )
        
        assert mock_run_agent.call_count == 1  # Exactly 1 call, no retries
        assert mock_sleep.call_count == 0
        self.fake_say.assert_called_with(
            text=":warning: Something went wrong! (Some other error)",
            thread_ts="123456.789"
        )
