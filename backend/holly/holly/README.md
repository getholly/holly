# Holly App

## Models

### LLM Model

The `LLM` model represents a Language Learning Model configuration with the following fields:

- `name`: The name of the language model
- `system_prompt`: The system prompt to use with this LLM
- `created_at`: Timestamp when the record was created (auto-filled)
- `updated_at`: Timestamp when the record was last updated (auto-filled)

## Management Commands

### populate_llms

This command populates the database with predefined LLM configurations for three AI agents:

1. **Gemini**: An agentic AI assistant for programming tasks
2. **Claude**: An agentic AI assistant for programming tasks
3. **Holly**: An agentic AI assistant for programming tasks

Each LLM is configured with a system prompt that enables them to function as autonomous agentic AI assistants capable of solving complete programming tasks using the ReAct process.

#### Usage

```bash
# Basic usage - create LLMs if they don't exist
python manage.py populate_llms

# Force recreation of LLMs even if they already exist
python manage.py populate_llms --force
```

#### Options

- `--force`: Force recreation of LLMs even if they already exist (default: False)

## Testing

The app includes tests for models and management commands:

```bash
# Run all tests
python manage.py test holly

# Run specific tests
python manage.py test holly.tests.test_populate_llms
```
