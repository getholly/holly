import { writable } from "svelte/store";
import { getRepos } from "$lib/apis/github/api.github";
import type { RepositorySchema } from "holly-api";
import type { GitHubRepository } from "$lib/types/githubTypes";

type RepositoriesStore = {
  repositories: GitHubRepository[];
  loading: boolean;
  error: string | null;
  lastFetched: Date | null;
};

// Helper function to map API response to our GitHubRepository type
function mapRepositorySchema(repo: RepositorySchema): GitHubRepository {
  return {
    id: repo.id,
    name: repo.name,
    full_name: repo.full_name,
    owner: {
      login: repo.owner.login,
      id: repo.owner.id,
      avatar_url: repo.owner.avatar_url,
      type: repo.owner.type,
    },
    private: repo.private,
    description: repo.description,
    stargazers_count: repo.stargazers_count,
    updated_at: repo.updated_at,
    created_at: repo.created_at,
    open_issues_count: repo.open_issues_count,
    language: repo.language || null,
    default_branch: repo.default_branch,
  };
}

function createRepositoriesStore() {
  const initialState: RepositoriesStore = {
    repositories: [],
    loading: false,
    error: null,
    lastFetched: null,
  };

  const { subscribe, set, update } = writable<RepositoriesStore>(initialState);

  return {
    subscribe,

    fetchRepositories: async (privateOnly: boolean = true) => {
      update((state) => ({ ...state, loading: true, error: null }));

      try {
        const repoSchema = await getRepos(privateOnly);

        // Map the RepositorySchema to our GitHubRepository type
        const repositories = Array.isArray(repoSchema)
          ? repoSchema.map(mapRepositorySchema)
          : [];

        set({
          repositories,
          loading: false,
          error: null,
          lastFetched: new Date(),
        });

        return repositories;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load repositories";

        update((state) => ({
          ...state,
          loading: false,
          error: errorMessage,
        }));

        throw err;
      }
    },

    reset: () => set(initialState),
  };
}

export const repositoriesStore = createRepositoriesStore();
