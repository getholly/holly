/**
 * GitHub installation related types
 */

/**
 * Represents a GitHub App installation
 */
export interface GitHubInstallation {
  installation_id: string;
  account_name: string;
  account_type: string; // "user" | "organization"
  installed_at: string; // ISO date string
}

/**
 * GitHub social account information
 */
export interface GitHubSocialAccount {
  login: string;
  avatar_url: string;
}

/**
 * Response from the installations API endpoint
 */
export interface GitHubInstallationsResponse {
  is_connected: boolean;
  social_account: GitHubSocialAccount | null;
  installations: GitHubInstallation[];
}
