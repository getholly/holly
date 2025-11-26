"""
Tests for the populate_llms management command.
"""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from holly.models import LLM


class PopulateLLMsCommandTest(TestCase):
    """Test case for the populate_llms management command."""

    def test_command_creates_llms(self) -> None:
        """Test that the command creates the expected LLMs."""
        # Make sure no LLMs exist initially
        assert LLM.objects.count() == 0

        # Call the command
        out = StringIO()
        call_command("populate_llms", stdout=out)

        # Check that the LLMs were created
        assert LLM.objects.count() == 3

        # Check that each expected LLM exists
        assert LLM.objects.filter(name="Gemini").exists()
        assert LLM.objects.filter(name="Claude").exists()
        assert LLM.objects.filter(name="Holly").exists()

        # Check that output message was written
        assert "Successfully populated LLM models" in out.getvalue()

    def test_command_skips_existing_llms(self) -> None:
        """Test that the command skips LLMs that already exist."""
        # Create an LLM that already exists
        LLM.objects.create(name="Gemini", system_prompt="Existing prompt")

        # Call the command
        out = StringIO()
        call_command("populate_llms", stdout=out)

        # Check that the LLMs were created/skipped as expected
        assert LLM.objects.count() == 3
        assert "already exists, skipping" in out.getvalue()

        # The existing LLM should not be modified
        gemini = LLM.objects.get(name="Gemini")
        assert gemini.system_prompt == "Existing prompt"

    def test_command_force_option(self) -> None:
        """Test that the --force option recreates existing LLMs."""
        # Create an LLM that already exists
        LLM.objects.create(name="Gemini", system_prompt="Existing prompt")

        # Call the command with --force
        out = StringIO()
        call_command("populate_llms", force=True, stdout=out)

        # Check that the LLMs were created/updated as expected
        assert LLM.objects.count() == 3
        assert "Updating existing LLM" in out.getvalue()

        # The existing LLM should be modified
        gemini = LLM.objects.get(name="Gemini")
        assert gemini.system_prompt != "Existing prompt"
