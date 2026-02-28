use crate::api::ApiClient;
use crate::error::Result;
use crate::models::*;

pub struct GithubService {
    api: ApiClient,
}

impl GithubService {
    pub fn new(api: ApiClient) -> Self { Self { api } }

    /// GET /_api/holly/git/ — list repositories (installations-level)
    pub async fn list_repositories(&self) -> Result<Vec<GitRepositoryResponse>> {
        self.api.get("/_api/holly/git/").await
    }

    /// GET /_api/holly/git/branches
    pub async fn branches(&self, data: RepositoryBranchesRequest) -> Result<BranchesResponse> {
        self.api.post("/_api/holly/git/branches", &data).await
    }

    /// POST /_api/holly/git/clone
    pub async fn clone_repo(&self, data: WorktreeRequest) -> Result<GenericResponse> {
        self.api.post("/_api/holly/git/clone", &data).await
    }

    /// POST /_api/holly/git/pull
    pub async fn pull(&self, data: PullRequest) -> Result<GenericResponse> {
        self.api.post("/_api/holly/git/pull", &data).await
    }

    /// POST /_api/holly/git/push
    pub async fn push(&self, data: PushRequest) -> Result<GenericResponse> {
        self.api.post("/_api/holly/git/push", &data).await
    }

    /// POST /_api/holly/git/commit
    pub async fn commit(&self, data: CommitRequest) -> Result<GenericResponse> {
        self.api.post("/_api/holly/git/commit", &data).await
    }

    /// POST /_api/users/github/oauth/initiate
    pub async fn oauth_initiate(&self, data: GitHubOAuthInitiateRequest) -> Result<GitHubOAuthInitiateResponse> {
        self.api.post("/_api/users/github/oauth/initiate", &data).await
    }

    /// POST /_api/users/github/oauth/callback
    pub async fn oauth_callback(&self, data: GitHubOAuthCallbackRequest) -> Result<GitHubOAuthCallbackResponse> {
        self.api.post("/_api/users/github/oauth/callback", &data).await
    }
}
