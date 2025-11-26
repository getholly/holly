import { gitApi } from "$lib/apis/api.config";
import { get } from "svelte/store";
import {
  type BranchesResponse,
  type CommitRequest,
  type GitRepositoryResponse,
  type PullRequest,
  type PushRequest,
  type RepositoryBranchesRequest,
  type WorktreeRequest,
  type HollyHollyApiViewsGitCloneRepositoryRequest,
  type HollyHollyApiViewsGitCommitChangesRequest,
  type HollyHollyApiViewsGitCreateWorktreeRequest,
  type HollyHollyApiViewsGitGetBranchesRequest,
  type HollyHollyApiViewsGitListBranchesRequest,
  type HollyHollyApiViewsGitPullChangesRequest,
  type HollyHollyApiViewsGitPushChangesRequest,
  GitApi,
} from "holly-api";

/**
 * Helper function to get the API client
 * @returns The git API client
 */
function getApiClient(): GitApi {
  return get(gitApi);
}

/**
 * Clone a GitHub repository in the mission container
 * @param missionId The UUID of the mission
 * @returns Promise<GitRepositoryResponse> Result of the clone operation
 */
export async function cloneRepository(
  missionId: string,
): Promise<GitRepositoryResponse> {
  try {
    const req: HollyHollyApiViewsGitCloneRepositoryRequest = {
      missionId: missionId,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsGitCloneRepository(req);
  } catch (error) {
    console.error(`Error cloning repository for mission ${missionId}:`, error);
    throw error;
  }
}

/**
 * Commit changes to a repository in the mission container
 * @param missionId The UUID of the mission
 * @param commitRequest Commit details including repository, branch, and message
 * @returns Promise<GitRepositoryResponse> Result of the commit operation
 */
export async function commitChanges(
  missionId: string,
  commitRequest: CommitRequest,
): Promise<GitRepositoryResponse> {
  try {
    const req: HollyHollyApiViewsGitCommitChangesRequest = {
      missionId: missionId,
      commitRequest: commitRequest,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsGitCommitChanges(req);
  } catch (error) {
    console.error(`Error committing changes for mission ${missionId}:`, error);
    throw error;
  }
}

/**
 * Create a git worktree for a specific branch in the mission container
 * @param missionId The UUID of the mission
 * @param worktreeRequest Worktree details including repository and branch information
 * @returns Promise<GitRepositoryResponse> Result of the worktree creation operation
 */
export async function createWorktree(
  missionId: string,
  worktreeRequest: WorktreeRequest,
): Promise<GitRepositoryResponse> {
  try {
    const req: HollyHollyApiViewsGitCreateWorktreeRequest = {
      missionId: missionId,
      worktreeRequest: worktreeRequest,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsGitCreateWorktree(req);
  } catch (error) {
    console.error(`Error creating worktree for mission ${missionId}:`, error);
    throw error;
  }
}

/**
 * Get a list of branches for a cloned repository in the mission container
 * @param missionId The UUID of the mission
 * @param repositoryBranchesRequest Repository details for branch listing
 * @returns Promise<BranchesResponse> The list of branches and other details
 */
export async function listBranches(
  missionId: string,
  repositoryBranchesRequest: RepositoryBranchesRequest,
): Promise<BranchesResponse> {
  try {
    const req: HollyHollyApiViewsGitListBranchesRequest = {
      missionId: missionId,
      repositoryBranchesRequest: repositoryBranchesRequest,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsGitListBranches(req);
  } catch (error) {
    console.error(`Error listing branches for mission ${missionId}:`, error);
    throw error;
  }
}

/**
 * Pull latest changes from remote repository in the mission container
 * @param missionId The UUID of the mission
 * @param pullRequest Pull details including repository and branch information
 * @returns Promise<GitRepositoryResponse> Result of the pull operation
 */
export async function pullChanges(
  missionId: string,
  pullRequest: PullRequest,
): Promise<GitRepositoryResponse> {
  try {
    const req: HollyHollyApiViewsGitPullChangesRequest = {
      missionId: missionId,
      pullRequest: pullRequest,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsGitPullChanges(req);
  } catch (error) {
    console.error(`Error pulling changes for mission ${missionId}:`, error);
    throw error;
  }
}

/**
 * Push local changes to remote repository from the mission container
 * @param missionId The UUID of the mission
 * @param pushRequest Push details including repository, branch, and force option
 * @returns Promise<GitRepositoryResponse> Result of the push operation
 */
export async function pushChanges(
  missionId: string,
  pushRequest: PushRequest,
): Promise<GitRepositoryResponse> {
  try {
    const req: HollyHollyApiViewsGitPushChangesRequest = {
      missionId: missionId,
      pushRequest: pushRequest,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsGitPushChanges(req);
  } catch (error) {
    console.error(`Error pushing changes for mission ${missionId}:`, error);
    throw error;
  }
}

/**
 * Get a list of branches for a repository using GitHub REST API with caching
 * @param repositoryBranchesRequest Repository details including owner and name
 * @returns Promise<BranchesResponse> The list of branches and other details
 */
export async function getBranches(
  repositoryBranchesRequest: RepositoryBranchesRequest,
): Promise<BranchesResponse> {
  try {
    const req: HollyHollyApiViewsGitGetBranchesRequest = {
      repositoryBranchesRequest: repositoryBranchesRequest,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsGitGetBranches(req);
  } catch (error) {
    console.error(
      `Error getting branches for repository ${repositoryBranchesRequest.repo_owner}/${repositoryBranchesRequest.repo_name}:`,
      error,
    );
    throw error;
  }
}
