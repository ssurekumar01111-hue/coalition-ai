import os
from unittest.mock import patch
import pytest
from agent.casey import get_model
import agent.casey


class TestCoalitionModel:
    def setup_method(self):
        # Reset the cached model before each test
        agent.casey._cached_model = None

    def teardown_method(self):
        # Reset the cached model after each test
        agent.casey._cached_model = None

    def test_get_model_google_priority(self):
        env_vars = {
            "GOOGLE_API_KEY": "fake_google_key",
            "ANTHROPIC_API_KEY": "fake_anthropic_key",
            "OPENAI_API_KEY": "fake_openai_key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            model = get_model()
            assert model == "google:gemini-2.5-flash"

    def test_get_model_anthropic_priority(self):
        env_vars = {
            "ANTHROPIC_API_KEY": "fake_anthropic_key",
            "OPENAI_API_KEY": "fake_openai_key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            model = get_model()
            assert model == "anthropic:claude-sonnet-4-6"

    def test_get_model_openai_fallback(self):
        env_vars = {
            "OPENAI_API_KEY": "fake_openai_key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            model = get_model()
            assert model == "openai:gpt-4.1-mini"

    def test_get_model_no_keys_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                get_model()
            assert "No AI provider configured" in str(exc_info.value)
            assert "GOOGLE_API_KEY" in str(exc_info.value)
            assert "ANTHROPIC_API_KEY" in str(exc_info.value)
            assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_get_model_caching(self):
        env_vars = {
            "OPENAI_API_KEY": "fake_openai_key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            model = get_model()
            assert model == "openai:gpt-4.1-mini"

        # Now, even if environment variables change or are cleared,
        # get_model should return the cached model.
        with patch.dict(os.environ, {}, clear=True):
            model = get_model()
            assert model == "openai:gpt-4.1-mini"
