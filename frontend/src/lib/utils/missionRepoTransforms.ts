import type { GitHubRepository } from "$lib/types/github/repository";
import type { MissionRepositoryResponseSchema } from "holly-api";
import type { RepoSyncSelection } from "$lib/services/missionRepoSync.service";
import { repositoriesStore } from "$lib/store/github/repositories.store";
import { get } from "svelte/store";
import type { RepoSelection } from "$lib/types/githubTypes";

/**
 * Transform mission repositories to GitMultiSelect initial selections format
 */
export function transformMissionReposToGitMultiSelect(
  missionRepos: MissionRepositoryResponseSchema[],
): RepoSelection[] {
  const repositories = get(repositoriesStore).repositories;
  const repoSelections: RepoSelection[] = [];

  console.log(
    "transformMissionReposToGitMultiSelect: Processing mission repos",
    missionRepos,
  );

  for (const missionRepo of missionRepos) {
    // Find matching GitHub repository from repositories store
    const fullName = `${missionRepo.username}/${missionRepo.repo}`;
    const githubRepo = repositories.find((repo) => repo.full_name === fullName);

    console.log(
      "transformMissionReposToGitMultiSelect: Processing repo",
      fullName,
      "Found in store:",
      !!githubRepo,
    );

    if (githubRepo) {
      repoSelections.push({
        repo: githubRepo,
        selectedBranch: missionRepo.repo || "main", // Use actual mission branch or default
        branches: [], // Will be populated when branches are fetched
        isLoadingBranches: false,
        errorBranches: undefined,
      });
    } else {
      // Create a minimal GitHubRepository object if not found in store
      const minimalRepo: GitHubRepository = {
        id: missionRepo.id,
        name: missionRepo.repo,
        full_name: fullName,
        owner: {
          login: missionRepo.username,
          id: 0, // Unknown
          avatar_url: "",
          type: "User",
          site_admin: false,
        },
        private: true, // Assume private since it's in a mission
        html_url: `https://github.com/${fullName}`,
        description: null,
        fork: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        pushed_at: new Date().toISOString(),
        clone_url: `https://github.com/${fullName}.git`,
        ssh_url: `git@github.com:${fullName}.git`,
        size: 0,
        stargazers_count: 0,
        watchers_count: 0,
        language: null,
        has_issues: true,
        has_projects: true,
        has_wiki: true,
        has_pages: false,
        forks_count: 0,
        archived: false,
        disabled: false,
        open_issues_count: 0,
        license: null,
        allow_forking: true,
        is_template: false,
        topics: [],
        visibility: "private",
        default_branch: missionRepo.branch || "main",
      };

      repoSelections.push({
        repo: minimalRepo,
        selectedBranch: missionRepo.branch || "main", // Use actual mission branch
        branches: [],
        isLoadingBranches: false,
        errorBranches: undefined,
      });
    }
  }

  console.log(
    "transformMissionReposToGitMultiSelect: Created selections",
    repoSelections,
  );
  return repoSelections;
}

/**
 * Transform GitMultiSelect selections to sync service format
 */
export function transformGitMultiSelectToSyncFormat(
  gitMultiSelectSelections: Array<{ repoFullName: string; branch: string }>,
): RepoSyncSelection[] {
  const repositories = get(repositoriesStore).repositories;

  return gitMultiSelectSelections.map((selection) => {
    // Find the repository ID from repositories store
    const githubRepo = repositories.find(
      (repo) => repo.full_name === selection.repoFullName,
    );

    return {
      repoFullName: selection.repoFullName,
      branch: selection.branch,
      repoId: githubRepo?.id,
    };
  });
}

/**
 * Check if two repository selection arrays are equivalent
 */
export function areRepoSelectionsEqual(
  selections1: RepoSyncSelection[],
  selections2: RepoSyncSelection[],
): boolean {
  if (selections1.length !== selections2.length) {
    return false;
  }

  const sorted1 = [...selections1].sort((a, b) =>
    a.repoFullName.localeCompare(b.repoFullName),
  );
  const sorted2 = [...selections2].sort((a, b) =>
    a.repoFullName.localeCompare(b.repoFullName),
  );

  return sorted1.every((repo1, index) => {
    const repo2 = sorted2[index];
    return (
      repo1.repoFullName === repo2.repoFullName && repo1.branch === repo2.branch
    );
  });
}

/**
 * Create a debounced function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number,
): (...args: Parameters<T>) => Promise<ReturnType<T>> {
  let timeout: ReturnType<typeof setTimeout> | null = null;

  return (...args: Parameters<T>): Promise<ReturnType<T>> => {
    return new Promise((resolve, reject) => {
      if (timeout) {
        clearTimeout(timeout);
      }

      timeout = setTimeout(async () => {
        try {
          const result = await func(...args);
          resolve(result);
        } catch (error) {
          reject(error);
        }
      }, wait);
    });
  };
}

/**
 * Get repository full name from GitHubRepository
 */
export function getRepoFullName(repo: GitHubRepository): string {
  return repo.full_name;
}

/**
 * Parse repository full name into owner and name parts
 */
export function parseRepoFullName(
  fullName: string,
): { owner: string; name: string } | null {
  const parts = fullName.split("/");
  if (parts.length !== 2) {
    return null;
  }
  return {
    owner: parts[0],
    name: parts[1],
  };
}

// Export types for external use
export type { RepoSelection, GitHubBranch };
