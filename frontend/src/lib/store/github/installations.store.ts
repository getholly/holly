import { writable } from "svelte/store";
import type {
  GitHubInstallation,
  GitHubSocialAccount,
} from "$lib/types/github/installation";
import { getInstallations } from "$lib/apis/github/api.github";
import type {
  InstallationSchema,
  InstallationsResponseSchema,
} from "holly-api";

type InstallationsStore = {
  isConnected: boolean;
  socialAccount: GitHubSocialAccount | null;
  installations: GitHubInstallation[];
  loading: boolean;
  error: string | null;
  lastFetched: Date | null;
};

// Helper function to map API response to our GitHubInstallation type
function mapInstallationSchema(
  installation: InstallationSchema,
): GitHubInstallation {
  return {
    installation_id: installation.installation_id.toString(),
    account_name: installation.account_name,
    account_type: installation.account_type,
    installed_at: installation.installed_at,
  };
}

function createInstallationsStore() {
  const initialState: InstallationsStore = {
    isConnected: false,
    socialAccount: null,
    installations: [],
    loading: false,
    error: null,
    lastFetched: null,
  };

  const { subscribe, set, update } = writable<InstallationsStore>(initialState);

  return {
    subscribe,

    fetchInstallations: async () => {
      update((state) => ({ ...state, loading: true, error: null }));

      try {
        const response: InstallationsResponseSchema = await getInstallations();

        // Map the API response to our frontend model
        const mappedInstallations = Array.isArray(response.installations)
          ? response.installations.map(mapInstallationSchema)
          : [];

        const socialAccount: GitHubSocialAccount | null =
          response.social_account
            ? {
                login: response.social_account.login,
                avatar_url: response.social_account.avatar_url,
              }
            : null;

        set({
          isConnected: response.is_connected,
          socialAccount,
          installations: mappedInstallations,
          loading: false,
          error: null,
          lastFetched: new Date(),
        });

        return mappedInstallations;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load installations";

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

export const installationsStore = createInstallationsStore();
