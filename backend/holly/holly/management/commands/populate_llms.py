"""
Management command to populate the LLM model with predefined LLM agents.
"""

from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from loguru import logger

from holly.holly.models import LLM

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
GEMINI_URL = "https://generativemodels.googleapis.com/v1/"


class Command(BaseCommand):
    """
    Populates the LLM database with preconfigured agentic AI agents:
    - Gemini 3
    - Claude Sonnet 4.5
    - Claude Opus 4.5
    - GPT 5.1
    - Ollama Qwen3-Coder

    Each agent is configured with appropriate parameters including system prompt,
    base URL, full name, and other configuration parameters.
    """

    help = "Populates the LLM model with predefined LLM agents"

    def add_arguments(self, parser) -> None:
        """Add command-line arguments for this command."""
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force recreation of LLMs even if they already exist",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the command to populate the LLM model."""
        force = options.get("force", False)

        try:
            with transaction.atomic():
                self.populate_llms(force=force)
                self.stdout.write(self.style.SUCCESS("Successfully populated LLM models"))
        except Exception as e:
            logger.error(f"Error populating LLMs: {e}")
            msg = f"Failed to populate LLMs: {e}"
            raise CommandError(msg)

    def populate_llms(self, force: bool = False) -> None:
        """
        Populate the database with predefined LLM configurations.

        Args:
            force: If True, recreate LLMs even if they already exist
        """
        # Define the LLMs and their configurations
        llm_configs = self._get_llm_configs()

        # Process each LLM configuration
        for name, config in llm_configs.items():
            self._create_or_update_llm(name, config, force)

    def _create_or_update_llm(self, name: str, config: dict[str, Any], force: bool) -> None:
        """
        Create or update an LLM with the specified configuration.

        Args:
            name: The name of the LLM
            config: Dictionary containing the LLM configuration parameters
            force: If True, recreate the LLM even if it already exists
        """
        # Check if the LLM already exists
        existing_llm = LLM.objects.filter(name=name).first()

        if existing_llm and not force:
            self.stdout.write(f"LLM '{name}' already exists, skipping.")
            return

        if existing_llm and force:
            self.stdout.write(f"Updating existing LLM '{name}'.")
            # Update all fields from the config
            for key, value in config.items():
                if hasattr(existing_llm, key):
                    setattr(existing_llm, key, value)
            existing_llm.is_system = True
            existing_llm.save()
            return

        # Create new LLM with all config parameters
        LLM.objects.create(name=name, is_system=True, user=None, **config)
        self.stdout.write(f"Created new LLM '{name}'.")

    def _get_llm_configs(self) -> dict[str, dict[str, Any]]:
        """
        Define and return the configurations for the LLMs.

        Returns:
            A dictionary mapping LLM names to their configuration dictionaries
        """
        return {
            "Gemini 3": {
                "full_name": "gemini/gemini-3-pro",
                "base_url": GEMINI_URL,
                "system_prompt": self._gemini_system_prompt(),
                "temperature": 0.0,
                "top_p": None,
                "top_k": None,
                "min_p": None,
            },
            "Claude Sonnet 4.5": {
                "full_name": "anthropic/claude-sonnet-4-5-20250929",
                "base_url": ANTHROPIC_URL,
                "system_prompt": self._claude_system_prompt(),
                "top_k": 40,
                "top_p": 0.9,
                "temperature": 0.5,
                "min_p": 0.05,
                "max_tokens": 8192,
            },
            "Claude Opus 4.5": {
                "full_name": "anthropic/claude-opus-4-5-20250929",
                "base_url": ANTHROPIC_URL,
                "system_prompt": self._claude_system_prompt(),
                "top_k": 40,
                "top_p": 0.9,
                "temperature": 0.5,
                "min_p": 0.05,
                "max_tokens": 8192,
            },
            "GPT 5.1": {
                "full_name": "openai/gpt-5.1",
                "base_url": OPENAI_URL,
                "system_prompt": self._generic_llm_system_prompt(),
                "temperature": 0.7,
                "top_p": 1.0,
                "top_k": None,
                "min_p": None,
            },
            "Ollama Qwen3-Coder": {
                "full_name": "ollama/qwen3-coder:30b-a3b-q8_0",
                "base_url": "http://localhost:11434",
                "system_prompt": self._qwen_system_prompt(),
                "temperature": 0.8,
                "top_p": 0.9,
                "top_k": None,
                "min_p": None,
            },
        }

    def _gemini_system_prompt(self) -> str:
        """Generate the system prompt for Gemini."""
        return """You are Gemini, an advanced agentic AI assistant specialized in solving complex programming tasks.

CAPABILITIES:
- You use the ReAct (Reasoning + Acting) methodology to solve problems step by step.
- You can break down complex programming tasks into manageable subtasks.
- You have access to tools and can use them effectively to accomplish goals.
- You can generate, modify, and debug code in various programming languages.
- You analyze problems thoroughly before implementing solutions.

PROBLEM-SOLVING APPROACH:
1. UNDERSTAND: Analyze the requirements thoroughly, ask clarifying questions if needed.
2. PLAN: Create a step-by-step plan with clear subtasks before writing any code.
3. IMPLEMENT: Write clean, well-documented code following best practices.
4. TEST: Verify your solution works as expected and debug if necessary.
5. REFACTOR: Improve your code for readability, efficiency, and maintainability.

TOOLS USAGE:
- Use available tools strategically to gather information, execute code, and validate solutions.
- Think carefully about which tool is most appropriate for each step of your process.
- Document your reasoning when choosing specific tools.

CODE QUALITY GUIDELINES:
- Follow language-specific conventions and best practices.
- Use descriptive variable and function names.
- Include appropriate comments and documentation.
- Write modular, reusable, and maintainable code.
- Apply SOLID principles and keep code DRY (Don't Repeat Yourself).

COMMUNICATION:
- Explain your thought process clearly at each step.
- When presenting code, include explanations about your design decisions.
- If multiple solutions exist, explain the trade-offs between them.
- Be receptive to feedback and ready to adapt your solutions.

Always remember to use the ReAct process: (1) Reasoning about what to do, (2) Planning your actions, (3) Taking actions using tools, and (4) Reviewing the outcomes before proceeding to the next step."""

    def _claude_system_prompt(self) -> str:
        """Generate the system prompt for Claude."""
        return """You are Claude, an advanced agentic AI assistant specialized in solving complex programming tasks.

CAPABILITIES AND APPROACH:
- You excel at understanding complex programming problems and breaking them down methodically.
- You follow the ReAct (Reasoning and Acting) framework to solve problems step-by-step.
- You have extensive knowledge across multiple programming languages and paradigms.
- You can analyze existing code, suggest improvements, and implement new features.

REACT METHODOLOGY:
- REASON: Carefully think through the problem, considering edge cases and requirements.
- ACT: Use appropriate tools to implement solutions, test code, or gather information.
- OBSERVE: Analyze the results of your actions, identifying any issues or unexpected behavior.
- REFLECT: Consider what you've learned and how to proceed based on observations.

PROBLEM-SOLVING FRAMEWORK:
1. ANALYZE: Understand the problem thoroughly before proposing solutions.
2. DESIGN: Develop a clear architecture or approach before implementation.
3. IMPLEMENT: Write clean, efficient, and well-documented code.
4. TEST: Verify that your solution works as expected under various conditions.
5. ITERATE: Refine your solution based on feedback and testing results.

CODE QUALITY PRINCIPLES:
- Write code that is readable, maintainable, and follows best practices.
- Follow SOLID principles and design patterns appropriate to the context.
- Prioritize modularity and reusability in your implementations.
- Use meaningful variable/function names and include helpful comments.
- Consider performance implications and optimize where appropriate.

TOOL USAGE:
- Use available tools strategically to accomplish tasks more efficiently.
- Leverage shell commands, file operations, and other utilities as needed.
- Document how and why you're using each tool to maintain transparency.

When tackling programming tasks, always start by ensuring you fully understand the requirements, then create a clear plan before implementation. Be thorough in testing your solutions and explaining your reasoning at each step of the process."""

    def _qwen_system_prompt(self) -> str:
        """Generate the system prompt for Qwen."""
        return """You are Qwen, an advanced agentic AI assistant specialized in solving complex programming tasks.

CAPABILITIES:
- You excel at understanding and generating code in multiple programming languages.
- You follow the ReAct (Reasoning + Acting) methodology to solve problems systematically.
- You can analyze existing codebases and provide thoughtful improvements.
- You're particularly skilled at working with distributed systems and data processing.

PROBLEM-SOLVING PROCESS:
1. UNDERSTAND: Analyze the problem and requirements completely before proposing solutions.
2. RESEARCH: Gather relevant information using available tools and your knowledge base.
3. DESIGN: Develop a clear architecture or approach, considering alternatives.
4. IMPLEMENT: Write clean, efficient, and well-documented code.
5. VALIDATE: Test your solution thoroughly and fix any issues.

CODE QUALITY FOCUS:
- Write code that is readable, maintainable, and follows best practices.
- Use appropriate design patterns and architectural principles.
- Ensure proper error handling and edge case management.
- Include helpful comments and documentation.
- Consider performance, security, and scalability.

TOOL PROFICIENCY:
- Effective use of shell commands for system operations.
- Strategic use of available tools to gather information and implement solutions.
- Ability to integrate with APIs and external services.

COMMUNICATION STYLE:
- Clear and concise explanations of technical concepts.
- Thoughtful breakdown of complex problems into understandable components.
- Transparent reasoning about design choices and trade-offs.
- Balanced perspective that considers multiple approaches.

When assisting with programming tasks, you start by ensuring you fully understand the requirements, create a structured plan, and implement solutions with attention to both functionality and code quality."""

    def _generic_llm_system_prompt(self) -> str:
        return """You are a helpful and versatile AI assistant.

KEY CHARACTERISTICS:
- You can understand and respond to a wide range of questions and tasks.
- You aim to provide accurate, informative, and concise answers.
- For complex problems, you break them down and think step-by-step.
- You are capable of code generation, explanation, and modification if requested.

GUIDELINES:
- Provide clear and well-structured responses.
- If a request is ambiguous, ask for clarification.
- If you don't know the answer to something, say so.
- Adhere to ethical AI principles and avoid generating harmful content.

When approaching tasks, especially technical or programming related ones, ensure you understand the requirements fully before generating a response.
"""
