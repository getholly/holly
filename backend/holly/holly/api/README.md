# Holly API

This directory contains the API implementation for the Holly app using django-ninja.

## API Endpoints

The API provides the following endpoints for interacting with LLM models:

### LLM Endpoints

- `GET /api/holly/llms/` - List all LLMs
- `GET /api/holly/llms/{llm_id}` - Get a specific LLM
- `POST /api/holly/llms/` - Create a new LLM
- `PUT /api/holly/llms/{llm_id}` - Update an existing LLM
- `DELETE /api/holly/llms/{llm_id}` - Delete an LLM

## Authentication

All API endpoints are protected with API key authentication. To access the API, include the `X-API-Key` header in your requests:

```
X-API-Key: your_api_key
```

The API key can be configured in your environment settings with the `API_KEY` variable.

## Documentation

API documentation is automatically generated and available at `/api/docs`.

## Example Usage

### List all LLMs

```python
import requests

response = requests.get(
    "http://localhost:8000/api/holly/llms/",
    headers={"X-API-Key": "your_api_key"}
)
llms = response.json()
```

### Create a new LLM

```python
import requests

response = requests.post(
    "http://localhost:8000/api/holly/llms/",
    headers={
        "X-API-Key": "your_api_key",
        "Content-Type": "application/json"
    },
    json={
        "name": "New LLM",
        "system_prompt": "Your system prompt"
    }
)
new_llm = response.json()
```
