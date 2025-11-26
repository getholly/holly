"""
Unit tests for the populate_llms management command.
"""

from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from holly.holly.management.commands.populate_llms import Command
from holly.holly.models import LLM


class PopulateLLMsCommandTest(TestCase):
    """Test cases for the populate_llms management command."""

    def setUp(self) -> None:
        """Set up test environment."""
        # Clear all LLMs before each test
        LLM.objects.all().delete()

    def test_command_creates_llms(self) -> None:
        """Test that the command creates all specified LLMs."""
        # Get the number of LLMs defined in the command
        command = Command()
        llm_configs = command._get_llm_configs()
        expected_count = len(llm_configs)

        # Run the command
        out = StringIO()
        call_command("populate_llms", stdout=out)

        # Check that the expected number of LLMs were created
        assert LLM.objects.count() == expected_count
        assert "Successfully populated LLM models" in out.getvalue()

    def test_command_skips_existing_llms(self) -> None:
        """Test that the command skips existing LLMs without --force."""
        # Create one LLM first
        LLM.objects.create(name="Gemini", system_prompt="Test prompt")

        # Get the initial count of LLMs
        LLM.objects.count()

        # Run the command
        out = StringIO()
        call_command("populate_llms", stdout=out)

        # Check that the LLM count increases by the number of new LLMs
        command = Command()
        expected_total = len(command._get_llm_configs())
        assert LLM.objects.count() == expected_total

        # Check that the output indicates skipping
        assert "already exists, skipping" in out.getvalue()

    def test_command_force_updates_existing_llms(self) -> None:
        """Test that the command updates existing LLMs with --force."""
        # Create an LLM with a test system prompt
        test_llm = LLM.objects.create(
            name="Gemini", system_prompt="Test prompt", full_name="test/model", base_url="http://test.url"
        )

        # Run the command with force
        out = StringIO()
        call_command("populate_llms", force=True, stdout=out)

        # Refresh the LLM from the database
        test_llm.refresh_from_db()

        # Check that the LLM was updated
        command = Command()
        gemini_config = command._get_llm_configs()["Gemini"]
        assert test_llm.system_prompt == gemini_config["system_prompt"]
        assert test_llm.full_name == gemini_config["full_name"]
        assert test_llm.base_url == gemini_config["base_url"]
        assert "Updating existing LLM" in out.getvalue()

    def test_command_handles_error(self) -> None:
        """Test that the command handles errors properly."""
        # Mock the populate_llms method to raise an exception
        with patch.object(Command, "populate_llms", side_effect=Exception("Test error")):
            with pytest.raises(CommandError):
                call_command("populate_llms")

    def test_llm_configs_structure(self) -> None:
        """Test that the LLM configurations have the correct structure."""
        command = Command()
        llm_configs = command._get_llm_configs()

        # Check that we have the expected LLMs
        expected_llms = ["Gemini", "Claude", "Holly", "Qwen", "Mistral"]
        for llm_name in expected_llms:
            assert llm_name in llm_configs

        # Check that each config has the required fields
        for llm_name, config in llm_configs.items():
            assert "full_name" in config
            assert "base_url" in config
            assert "system_prompt" in config
