import difflib

import pytest

from holly.github_ext.services import mermaid_fix

simple_missing_quotes = """
flowchart TB
  A --> B[message()]
"""

simple_missing_quotes_expected = """
```mermaid
flowchart TB
  A --> B["message()"]
```
"""

missing_quotes = """
flowchart TB
	%% System Boundaries
	subgraph Frontend
		direction TB
		sveltekit[SvelteKit App]
		apiClient["API Client (frontend/gen/openapi)"]
		components[Svelte Components]
		l10n[Localization (frontend/src/l10n)]
		store[Svelte Stores]

		sveltekit -- uses --> apiClient
		sveltekit -- uses --> components
		sveltekit -- uses --> l10n
		sveltekit -- uses --> store
		components --> apiClient
	end

	subgraph "Backend (holly)"
		direction TB
		fastapi_server[fastapi_server.py (FastAPI OAuth)]
		django_app[holly Django App]
		llmrepo_lib[llmrepo_lib]
		treesitter_lib[treesitter]
		scripts_backend[scripts]
		githubme_githubme[holly]
		
		githubme_home[holly.home]
		githubme_github_ext[holly.github_ext]
		githubme_users[holly.users]
		githubme_background_tasks[holly.background_tasks]

		fastapi_server -- calls --> django_app
		django_app -- uses --> llmrepo_lib
		django_app -- uses --> treesitter_lib
		django_app --> githubme_githubme
		
		githubme_githubme --> githubme_home
		githubme_githubme --> githubme_github_ext
		githubme_githubme --> githubme_users
		githubme_githubme --> githubme_background_tasks
	end

	sveltekit -- calls --> fastapi_server
"""
missing_quotes_expected = """
```mermaid
flowchart TB
	%% System Boundaries
	subgraph Frontend
		direction TB
		sveltekit[SvelteKit App]
		apiClient["API Client (frontend/gen/openapi)"]
		components[Svelte Components]
		l10n["Localization (frontend/src/l10n)"]
		store[Svelte Stores]

		sveltekit -- uses --> apiClient
		sveltekit -- uses --> components
		sveltekit -- uses --> l10n
		sveltekit -- uses --> store
		components --> apiClient
	end

	subgraph "Backend (holly)"
		direction TB
		fastapi_server["fastapi_server.py (FastAPI OAuth)"]
		django_app[holly Django App]
		llmrepo_lib[llmrepo_lib]
		treesitter_lib[treesitter]
		scripts_backend[scripts]
		githubme_githubme[holly]
		
		githubme_home[holly.home]
		githubme_github_ext[holly.github_ext]
		githubme_users[holly.users]
		githubme_background_tasks[holly.background_tasks]

		fastapi_server -- calls --> django_app
		django_app -- uses --> llmrepo_lib
		django_app -- uses --> treesitter_lib
		django_app --> githubme_githubme
		
		githubme_githubme --> githubme_home
		githubme_githubme --> githubme_github_ext
		githubme_githubme --> githubme_users
		githubme_githubme --> githubme_background_tasks
	end

	sveltekit -- calls --> fastapi_server
```
"""


def show_diff(a: str, b: str) -> str:
    """Generate a diff between two strings and return a formatted string"""
    # Split both strings into lines
    a_lines = a.splitlines(keepends=True)
    b_lines = b.splitlines(keepends=True)

    # Generate unified diff
    diff = difflib.unified_diff(
        a_lines,
        b_lines,
        fromfile="Expected",
        tofile="Actual",
        n=3,  # Context lines
    )

    return "".join(diff)


@pytest.mark.parametrize(
    ("mermaid_broken", "mermaid_expected"),
    [(simple_missing_quotes, simple_missing_quotes_expected), (missing_quotes, missing_quotes_expected)],
)
def test_mermaid_fix(mermaid_broken: str, mermaid_expected: str):
    fixed = mermaid_fix.fix_mermaid_markdown(mermaid_broken)
    # If assertion fails, show a clear diff of what's different
    if mermaid_expected.strip() != fixed.strip():
        diff_str = show_diff(mermaid_expected.strip(), fixed.strip())
        pytest.fail(f"Mermaid fix produced unexpected result. Differences:\n{diff_str}")

    assert fixed.strip() == mermaid_expected.strip()
