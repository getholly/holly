# Holly MVP Test Suite

This test suite provides comprehensive coverage for the Holly MVP flow, ensuring that the core functionality works correctly from GitHub App connection through to git push.

## Overview

The test suite is organized into three layers:

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test component interactions (to be completed)
3. **E2E Tests** - Test complete user workflows

## Test Coverage

### ✅ Completed Tests

#### 1. Factory Boy Factories (`factories.py`)

Provides consistent test data generation for all models:

- `UserFactory` - Create test users
- `SocialAccountFactory` - GitHub OAuth accounts
- `GitHubAppInstallationFactory` - GitHub App installations
- `RepositoryDetailFactory` - Repository metadata
- `LLMFactory` - LLM configurations
- `MissionFactory` - Missions with repositories
- `MissionConversationFactory` - Conversations
- `MessageFactory` - Chat messages
- `KnowledgeFactory` - Knowledge items
- `ToolsFactory` - Tool configurations

**Helper Functions:**
- `create_complete_mission()` - Create fully configured mission
- `create_mission_with_conversation()` - Mission ready for messaging
- `create_github_user_with_installation()` - User with GitHub App

#### 2. Pytest Fixtures (`conftest.py`)

Comprehensive mock fixtures for all external dependencies:

**Docker Mocking:**
- `mock_docker_container` - Mocked Docker container
- `mock_docker_client` - Mocked Docker SDK client

**Hilly API Mocking:**
- `mock_hilly_api_client` - Complete Hilly REST API mock
- `mock_hilly_health_response` - Health check responses
- `mock_hilly_clone_response` - Git clone responses
- `mock_hilly_worktree_response` - Worktree creation responses
- `mock_hilly_commit_response` - Commit responses
- `mock_hilly_push_response` - Push responses

**GitHub App Mocking:**
- `mock_github_app_integration` - GitHub App service mock
- `mock_github_installation_token` - Installation token responses
- `mock_github_repositories` - Repository list responses

**LLM Provider Mocking:**
- `mock_openai_client` - OpenAI API mock
- `mock_anthropic_client` - Anthropic API mock

**Redis Mocking:**
- `mock_redis` - Redis client for SSE events

**Sample Data:**
- `sample_repo_tree` - Repository file structure
- `sample_mission_env_vars` - Container environment variables
- `webhook_payload_*` - Various webhook payloads

#### 3. Unit Tests

**`unit/backend/test_github_app_integration.py`** (330 lines)

Tests GitHub App integration (primary auth method):
- `TestGitHubAppInstallationModel` - Installation model CRUD
- `TestAuthUtils` - Auth utility functions
- `TestGetBestGitHubAuth` - GitHub App vs OAuth priority
- `TestGitHubAppService` - Repository access and operations

Key scenarios:
- ✅ GitHub App installation creation and uniqueness
- ✅ Installation token generation
- ✅ Repository listing via GitHub App
- ✅ Repository URL generation with auth
- ✅ Pull request creation
- ✅ Error handling for API failures
- ✅ GitHub App preferred over OAuth

**`unit/backend/test_mission_models.py`** (420 lines)

Tests Mission model behavior:
- `TestMissionReposModel` - Repository junction model
- `TestMissionModel` - Basic mission operations
- `TestMissionStateTransitions` - State machine
- `TestMissionContainerManagement` - Container tracking
- `TestMissionAccessControl` - Owner/collaborator access
- `TestMissionHelperMethods` - Utility methods
- `TestMissionRequirements` - Requirements JSONField
- `TestMissionOrderingAndTimestamps` - Ordering and auto-timestamps

Key scenarios:
- ✅ Mission CRUD operations
- ✅ State transitions (DRAFT→PROVISIONING→READY→IN_PROGRESS→COMPLETED)
- ✅ Repository relationships (many-to-many)
- ✅ Collaborator access control
- ✅ Container lifecycle tracking
- ✅ Mission summary generation

#### 4. End-to-End Tests

**`e2e/backend/test_mvp_flow.py`** (380 lines)

**Critical MVP Flow Test** - Complete user journey:

```
1. User with GitHub App installation ✅
2. List repositories from installation ✅
3. Create mission with repos + model ✅
4. Start mission container (mocked Docker) ✅
5. Container initialization webhook → READY ✅
6. Create conversation ✅
7. Send user message ✅
8. Hilly processes and responds (mocked) ✅
9. Git commit webhook ✅
10. Git push webhook ✅
11. Task completion webhook ✅
12. Verify final state ✅
```

Test methods:
- `test_complete_mvp_flow()` - Full flow with 2 repositories
- `test_mvp_flow_with_single_repository()` - Simpler single repo case
- `test_mvp_flow_user_can_access_own_mission()` - Access control
- `test_error_handling_in_mvp_flow()` - Container init failure

**`e2e/backend/test_branch_creation_mvp.py`** (380 lines)

**Critical Branch Creation Test** - Git workflow:

```
1. Mission specifies branch "holly/feature-x" ✅
2. Container clones base branch (main) ✅
3. Container creates worktree for mission branch ✅
4. Changes committed to mission branch ✅
5. Mission branch pushed to remote ✅
6. Remote branch created successfully ✅
```

Test methods:
- `test_branch_creation_end_to_end()` - Complete branch lifecycle
- `test_multiple_repos_same_branch()` - Cross-repo branch sync
- `test_branch_name_validation()` - Branch naming patterns
- `test_branch_creation_failure_handling()` - Worktree errors
- `test_push_failure_handling()` - Push permission errors
- `test_branch_lifecycle_tracking()` - Event tracking

## Running the Tests

### Run All Tests

```bash
cd tests
pytest
```

### Run Specific Test Suites

```bash
# Unit tests only
pytest unit/

# E2E tests only
pytest e2e/

# Backend tests only
pytest unit/backend/ e2e/backend/

# Specific test file
pytest e2e/backend/test_mvp_flow.py

# Specific test method
pytest e2e/backend/test_mvp_flow.py::TestCompleteMVPFlow::test_complete_mvp_flow

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=holly.holly --cov=holly.github_ext --cov-report=html
```

### Run Tests with Markers

```bash
# Run only async tests
pytest -m asyncio

# Run Django DB tests
pytest -m django_db

# Run unit tests only
pytest -m unit

# Run e2e tests only
pytest -m e2e
```

## Test Structure

```
tests/
├── factories.py                          # Factory Boy factories (440 lines)
├── conftest.py                          # Pytest fixtures (445 lines)
├── pytest.ini                           # Pytest configuration
├── README.md                            # This file
├── unit/
│   └── backend/
│       ├── test_github_app_integration.py   # GitHub App tests (330 lines)
│       └── test_mission_models.py           # Mission model tests (420 lines)
├── e2e/
│   └── backend/
│       ├── test_mvp_flow.py                 # Complete MVP flow (380 lines)
│       └── test_branch_creation_mvp.py      # Branch creation (380 lines)
├── integration/
│   └── backend/                         # Placeholder for future tests
└── frontend/                            # Placeholder for frontend tests
    └── hilly/                           # Placeholder for hilly tests

Total: ~2,395 lines of test code
```

## Key Testing Patterns

### 1. Use Factories for Test Data

```python
from tests.factories import MissionFactory, UserFactory

def test_something():
    user = UserFactory()
    mission = MissionFactory(owner=user)
    assert mission.owner == user
```

### 2. Use Fixtures for Mocking

```python
def test_with_docker(mock_docker_client):
    # Docker is automatically mocked
    # No real containers created
    pass

def test_with_hilly(mock_hilly_api_client):
    # Hilly API is mocked with realistic responses
    pass
```

### 3. Test State Transitions

```python
mission = MissionFactory(state=Mission.State.DRAFT)
mission.state = Mission.State.PROVISIONING
mission.save()
assert mission.state == Mission.State.PROVISIONING
```

### 4. Test Webhooks

```python
from holly.holly.services.webhook_handler import WebhookHandler

webhook_handler = WebhookHandler()
result = webhook_handler.process_webhook(
    mission_id=str(mission.id),
    job_id="init",
    status="completed",
    data={"message": "Init complete"},
    timestamp="2025-11-11T12:00:00Z",
)
```

## What These Tests Guarantee

### ✅ MVP Flow Coverage

1. **GitHub App Integration**
   - Installation creation and management
   - Repository access via installation tokens
   - Token generation and authentication
   - Fallback to OAuth when needed

2. **Mission Management**
   - Mission creation with repositories
   - State machine transitions
   - Container lifecycle tracking
   - Access control (owner/collaborators)

3. **Container Orchestration**
   - Container creation (mocked)
   - Environment variable configuration
   - Health checks
   - Webhook-based state updates

4. **Git Operations** (via webhooks)
   - Repository cloning
   - Branch creation (worktrees)
   - Commit tracking
   - Push to remote

5. **Conversation Flow**
   - Conversation creation
   - Message exchange
   - Status tracking

6. **Webhook Processing**
   - Initialization webhooks
   - Git operation webhooks
   - Task completion webhooks
   - Error webhooks
   - Redis event publishing

### ⚠️ Not Yet Tested (Future Work)

- Unit tests for mission service layer
- Unit tests for conversation models
- Unit tests for webhook handler
- Integration tests for GitHub App flow
- Integration tests for mission lifecycle
- Integration tests for conversation flow
- Integration tests for git orchestration
- Integration tests for webhook delivery
- E2E tests for error scenarios
- Frontend integration tests
- Actual Hilly container tests

## Troubleshooting

### Common Issues

**ImportError: No module named 'tests'**
```bash
# Ensure you're in the correct directory
cd tests
# Or run from project root with proper PYTHONPATH
PYTHONPATH=. pytest tests/
```

**Docker-related test failures**
```python
# Make sure mock_docker_client fixture is used
def test_something(mock_docker_client):
    # Docker operations are mocked
    pass
```

**Database errors**
```python
# Ensure @pytest.mark.django_db is used
@pytest.mark.django_db
def test_database_operation():
    user = UserFactory()  # Requires DB access
```

**Async test failures**
```python
# Use @pytest.mark.asyncio for async tests
@pytest.mark.asyncio
async def test_async_operation():
    result = await some_async_function()
```

## Next Steps

To complete the test suite, implement:

1. **Integration Tests** - Test component interactions
2. **Service Layer Tests** - Test business logic services
3. **Webhook Handler Tests** - Comprehensive webhook processing tests
4. **Error Scenario Tests** - Test all failure modes
5. **Performance Tests** - Test under load
6. **Frontend Tests** - Playwright/Vitest integration tests

## Contributing

When adding new tests:

1. Use existing factories and fixtures
2. Follow the naming convention: `test_<what_it_does>()`
3. Add docstrings explaining what's being tested
4. Mock external dependencies (Docker, Hilly, GitHub, LLMs)
5. Test both success and failure scenarios
6. Keep tests focused and isolated
7. Place tests in appropriate directories (unit/, e2e/, integration/)

## References

- Django Testing: https://docs.djangoproject.com/en/stable/topics/testing/
- pytest-django: https://pytest-django.readthedocs.io/
- Factory Boy: https://factoryboy.readthedocs.io/
- pytest fixtures: https://docs.pytest.org/en/stable/fixture.html
