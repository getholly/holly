# Analytics Module Documentation

## Overview

The Analytics module provides tracking and analytical capabilities for the GitHubMe application. It records user interactions with repositories and their usage of the LLM query features, providing valuable insights into user behavior and platform usage.

## Features

- **Repository Tracking**: Records basic information about repositories accessed through the platform
- **View Tracking**: Monitors when users view specific repositories
- **LLM Query Tracking**: Logs queries made to LLM models about repositories
- **Admin Interface**: Provides administrative views for reviewing analytics data

## Models

### Repository

Tracks repositories that have been analyzed through the platform:

- `username`: Repository owner's GitHub username
- `repo_name`: Name of the repository
- `private`: Boolean flag indicating if the repository is private
- `timestamp`: When the repository was first tracked

### RepoView

Records when a user views a repository through the `analyse_repo` view:

- `user`: Reference to the User model
- `repo`: Reference to the Repository model
- `timestamp`: When the view occurred

### LLMQuery

Tracks usage of LLM queries about GitHub repositories:

- `user`: Reference to the User model
- `repo`: Reference to the Repository model
- `query_text`: The text content of the user's query
- `model_name`: Name of the LLM model used
- `timestamp`: When the query was made

## Integration

The analytics module is integrated at key points in the application flow:

1. **Repository Views**: Tracked automatically when a user accesses the `analyse_repo` view
2. **LLM Queries**: Tracked via a pipeline step in the LLM request pipeline

## Pipeline Integration

The module includes a `TrackLLMQueryStep` pipeline step that can be added to LLM request pipelines. This step:

- Records successful LLM queries
- Uses a fault-tolerant implementation that won't break the pipeline if analytics tracking fails
- Captures metadata about the query including user, repository, query text, and model used

## Admin Interface

All analytics models are registered with the Django admin interface, providing:

- Comprehensive filters and search functionality
- Clickable repository links to GitHub
- Sanitized preview of query texts
- Chronological organization of data with date hierarchies

## Usage

Analytics data is collected automatically and requires no explicit user action. The data can be accessed through the Django admin interface under the "Analytics" section.
