// src/lib/githubTypes.ts
export interface GitHubBranch {
  name: string;
  commit: { sha: string; url: string };
  protected: boolean;
}

export interface GitHubRepositoryOwner {
  login: string;
  id: number;
  avatar_url: string;
  type: string;
}

export interface GitHubRepository {
  id: number;
  name: string;
  full_name: string;
  owner: GitHubRepositoryOwner;
  private: boolean;
  description: string | null | undefined;
  stargazers_count: number | undefined;
  updated_at: string | null | undefined;
  created_at: string | null | undefined;
  language: string | null;
  open_issues_count: number | undefined;
  default_branch: string;
}

export interface RepoSelection {
  repo: GitHubRepository;
  selectedBranch: string | null;
  branches: GitHubBranch[];
  isLoadingBranches: boolean;
  errorBranches?: string;
}

// --- Stub Data ---

export const fakeRepos: GitHubRepository[] = [
  {
    id: 1,
    name: "repo-alpha",
    full_name: "owner1/repo-alpha",
    private: false,
    owner: { id: 1, login: "owner1", avatar_url: "", type: "Organization" },
    default_branch: "main",
    description: "A sample public repository",
    stargazers_count: 42,
    updated_at: "2023-10-01T12:00:00Z",
    created_at: "2023-01-01T12:00:00Z",
    language: "JavaScript",
    open_issues_count: 5,
  },
  {
    id: 2,
    name: "repo-beta",
    full_name: "owner1/repo-beta",
    private: true,
    owner: { id: 2, login: "owner12", avatar_url: "", type: "Organization" },
    default_branch: "develop",
    description: "A sample public repository",
    stargazers_count: 42,
    updated_at: "2023-10-01T12:00:00Z",
    created_at: "2023-01-01T12:00:00Z",
    language: "JavaScript",
    open_issues_count: 5,
  },
  {
    id: 3,
    name: "omega-project",
    full_name: "owner2/omega-project",
    private: false,
    owner: { id: 3, login: "owner3", avatar_url: "", type: "Organization" },
    default_branch: "master",
    description: "A sample public repository",
    stargazers_count: 42,
    updated_at: "2023-10-01T12:00:00Z",
    created_at: "2023-01-01T12:00:00Z",
    language: "JavaScript",
    open_issues_count: 5,
  },
  {
    id: 4,
    name: "gamma-lib",
    full_name: "owner1/gamma-lib",
    private: false,
    owner: { id: 4, login: "owner4", avatar_url: "", type: "Organization" },
    default_branch: "main",
    description: "A sample public repository",
    stargazers_count: 42,
    updated_at: "2023-10-01T12:00:00Z",
    created_at: "2023-01-01T12:00:00Z",
    language: "JavaScript",
    open_issues_count: 5,
  },
  {
    id: 5,
    name: "another-one",
    full_name: "owner3/another-one",
    private: true,
    owner: { id: 5, login: "owner5", avatar_url: "", type: "Organization" },
    default_branch: "release-v1.0",
    description: "A sample public repository",
    stargazers_count: 42,
    updated_at: "2023-10-01T12:00:00Z",
    created_at: "2023-01-01T12:00:00Z",
    language: "JavaScript",
    open_issues_count: 5,
  },
];

export const fakeBranches: Record<string, GitHubBranch[]> = {
  "owner1/repo-alpha": [
    { name: "main", commit: { sha: "abc", url: "" }, protected: true },
    { name: "feature/x", commit: { sha: "def", url: "" }, protected: false },
    { name: "bugfix/y", commit: { sha: "ghi", url: "" }, protected: false },
  ],
  "owner1/repo-beta": [
    { name: "develop", commit: { sha: "123", url: "" }, protected: false },
    {
      name: "release/candidate",
      commit: { sha: "456", url: "" },
      protected: false,
    },
  ],
  "owner2/omega-project": [
    { name: "master", commit: { sha: "789", url: "" }, protected: true },
    { name: "docs-update", commit: { sha: "101", url: "" }, protected: false },
  ],
  "owner1/gamma-lib": [
    { name: "main", commit: { sha: "xyz", url: "" }, protected: true },
  ],
  "owner3/another-one": [
    { name: "release-v1.0", commit: { sha: "aaa", url: "" }, protected: true },
    { name: "hotfix/z", commit: { sha: "bbb", url: "" }, protected: false },
  ],
};

// --- Stub Functions ---

export const stubFetchRepositories = (): Promise<GitHubRepository[]> => {
  console.log("STUB: Fetching repositories...");
  return new Promise((resolve) => {
    setTimeout(() => {
      console.log("STUB: Repositories fetched.");
      resolve([...fakeRepos]); // Return a copy
    }, 1000); // Simulate network delay
  });
};

export const stubFetchBranches = (
  repoFullName: string,
): Promise<GitHubBranch[]> => {
  console.log(`STUB: Fetching branches for ${repoFullName}...`);
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const branches = fakeBranches[repoFullName];
      if (branches) {
        console.log(`STUB: Branches for ${repoFullName} fetched.`);
        resolve([...branches]); // Return a copy
      } else {
        console.warn(`STUB: No fake branches found for ${repoFullName}.`);
        // Simulate not found or an error condition occasionally
        if (Math.random() > 0.9) {
          reject(
            new Error(`STUB: Failed to fetch branches for ${repoFullName}`),
          );
        } else {
          resolve([]); // Return empty array if no specific fake data exists
        }
      }
    }, 800); // Simulate network delay
  });
};
