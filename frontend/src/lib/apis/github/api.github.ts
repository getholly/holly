import { githubApi } from "$lib/apis/api.config";
import type {
  GitHubApi,
  HollyGithubExtApiRouterListRepositoriesRequest,
  InstallationsResponseSchema,
  RepositorySchema,
  InstallationUrlResponseSchema,
  InstallationCallbackRequestSchema,
  InstallationCallbackResponseSchema,
  InstallationStatusResponseSchema,
  HollyGithubExtApiRouterGetInstallationStatusRequest,
  HollyGithubExtApiRouterHandleInstallationCallbackRequest,
} from "holly-api";
import { get } from "svelte/store";

function getApiClient(): GitHubApi {
  return get(githubApi);
}

export async function getRepos(
  privateOnly: boolean = true,
): Promise<RepositorySchema[]> {
  const req: HollyGithubExtApiRouterListRepositoriesRequest = {
    privateOnly: privateOnly,
  };
  return await getApiClient().hollyGithubExtApiRouterListRepositories(req);
}

export async function getInstallations(): Promise<InstallationsResponseSchema> {
  return await getApiClient().hollyGithubExtApiRouterListInstallations();
}

export async function getInstallationUrl(): Promise<InstallationUrlResponseSchema> {
  return await getApiClient().hollyGithubExtApiRouterGetInstallationUrl();
}

export async function handleInstallationCallback(
  request: InstallationCallbackRequestSchema,
): Promise<InstallationCallbackResponseSchema> {
  const req: HollyGithubExtApiRouterHandleInstallationCallbackRequest = {
    installationCallbackRequestSchema: request,
  };
  return await getApiClient().hollyGithubExtApiRouterHandleInstallationCallback(
    req,
  );
}

export async function getInstallationStatus(
  installationId: string,
): Promise<InstallationStatusResponseSchema> {
  const req: HollyGithubExtApiRouterGetInstallationStatusRequest = {
    installationId: installationId,
  };
  return await getApiClient().hollyGithubExtApiRouterGetInstallationStatus(req);
}
