import { llmKeysApi } from "$lib/apis/api.config";
import type {
  UserLLMApiKeySchema,
  UserLLMApiKeyCreateSchema,
  UserLLMApiKeyUpdateSchema,
} from "$lib/types/user_llm_api_key";
import type {
  LLMKeysApi,
  HollyHollyApiViewsUserLlmApiKeyViewsListApiKeysRequest,
  HollyHollyApiViewsUserLlmApiKeyViewsCreateApiKeyRequest,
  HollyHollyApiViewsUserLlmApiKeyViewsUpdateApiKeyRequest,
  HollyHollyApiViewsUserLlmApiKeyViewsDeleteApiKeyRequest,
} from "holly-api";
import { get } from "svelte/store";

// Error types for better error handling
export class LLMKeysApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public originalError?: unknown,
  ) {
    super(message);
    this.name = "LLMKeysApiError";
  }
}

export class ValidationError extends LLMKeysApiError {
  constructor(
    message: string,
    public field?: string,
  ) {
    super(message);
    this.name = "ValidationError";
  }
}

// Configuration for retry logic
const RETRY_CONFIG = {
  maxRetries: 3,
  baseDelay: 1000, // 1 second
  maxDelay: 5000, // 5 seconds
};

// Helper function to get API client
function getApiClient(): LLMKeysApi {
  return get(llmKeysApi);
}

// Validation helpers
function validateApiKeyId(apiKeyId: number): void {
  if (!apiKeyId || apiKeyId <= 0) {
    throw new ValidationError("Invalid API key ID", "apiKeyId");
  }
}

function validateCreateRequest(data: UserLLMApiKeyCreateSchema): void {
  if (!data.llm_id || data.llm_id <= 0) {
    throw new ValidationError("Invalid LLM ID", "llm_id");
  }
  if (!data.api_key || data.api_key.trim().length === 0) {
    throw new ValidationError("API key is required", "api_key");
  }
  if (data.api_key.length < 10) {
    throw new ValidationError("API key is too short", "api_key");
  }
}

function validateUpdateRequest(data: UserLLMApiKeyUpdateSchema): void {
  if (!data.api_key || data.api_key.trim().length === 0) {
    throw new ValidationError("API key is required", "api_key");
  }
  if (data.api_key.length < 10) {
    throw new ValidationError("API key is too short", "api_key");
  }
}

function validatePaginationParams(page?: number, pageSize?: number): void {
  if (page !== undefined && page < 1) {
    throw new ValidationError("Page number must be greater than 0", "page");
  }
  if (pageSize !== undefined && (pageSize < 1 || pageSize > 100)) {
    throw new ValidationError(
      "Page size must be between 1 and 100",
      "pageSize",
    );
  }
}

// Retry logic helper
async function withRetry<T>(
  operation: () => Promise<T>,
  operationName: string,
): Promise<T> {
  let lastError: unknown;

  for (let attempt = 1; attempt <= RETRY_CONFIG.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;

      // Don't retry on validation errors or client errors (4xx)
      if (error instanceof ValidationError) {
        throw error;
      }

      // Check if it's a network error or server error (5xx) that we should retry
      const shouldRetry =
        attempt < RETRY_CONFIG.maxRetries &&
        (error instanceof TypeError || // Network errors
          (error as any)?.status >= 500); // Server errors

      if (!shouldRetry) {
        break;
      }

      // Calculate delay with exponential backoff
      const delay = Math.min(
        RETRY_CONFIG.baseDelay * Math.pow(2, attempt - 1),
        RETRY_CONFIG.maxDelay,
      );

      console.warn(
        `${operationName} attempt ${attempt} failed, retrying in ${delay}ms:`,
        error,
      );
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  // If we get here, all retries failed
  const errorMessage = `${operationName} failed after ${RETRY_CONFIG.maxRetries} attempts`;
  throw new LLMKeysApiError(
    errorMessage,
    (lastError as any)?.status,
    lastError,
  );
}

// Error handler wrapper
function handleApiError(error: unknown, operation: string): never {
  if (error instanceof ValidationError || error instanceof LLMKeysApiError) {
    throw error;
  }

  const apiError = error as any;
  const status = apiError?.status || apiError?.response?.status;
  const message = apiError?.message || `${operation} failed`;

  throw new LLMKeysApiError(message, status, error);
}

/**
 * List all LLM API keys for the current user with pagination support
 * @param page - Page number (default: 1)
 * @param pageSize - Number of items per page (default: 25, max: 100)
 * @returns Promise<UserLLMApiKeySchema[]>
 * @throws {ValidationError} When pagination parameters are invalid
 * @throws {LLMKeysApiError} When the API request fails
 */
export const listApiKeys = async (
  page: number = 1,
  pageSize: number = 25,
): Promise<UserLLMApiKeySchema[]> => {
  try {
    // Validate input parameters
    validatePaginationParams(page, pageSize);

    return await withRetry(async () => {
      const request: HollyHollyApiViewsUserLlmApiKeyViewsListApiKeysRequest = {
        page,
        pageSize,
      };

      return await getApiClient().hollyHollyApiViewsUserLlmApiKeyViewsListApiKeys(
        request,
      );
    }, "listApiKeys");
  } catch (error) {
    handleApiError(error, "List API keys");
  }
};

/**
 * Create a new LLM API key
 * @param data - The API key creation data
 * @returns Promise<UserLLMApiKeySchema>
 * @throws {ValidationError} When input data is invalid
 * @throws {LLMKeysApiError} When the API request fails
 */
export const createApiKey = async (
  data: UserLLMApiKeyCreateSchema,
): Promise<UserLLMApiKeySchema> => {
  try {
    // Validate input data
    validateCreateRequest(data);

    return await withRetry(async () => {
      const request: HollyHollyApiViewsUserLlmApiKeyViewsCreateApiKeyRequest = {
        userLLMApiKeyCreateSchema: data,
      };

      return await getApiClient().hollyHollyApiViewsUserLlmApiKeyViewsCreateApiKey(
        request,
      );
    }, "createApiKey");
  } catch (error) {
    handleApiError(error, "Create API key");
  }
};

/**
 * Update an existing LLM API key
 * @param apiKeyId - The ID of the API key to update
 * @param data - The API key update data
 * @returns Promise<UserLLMApiKeySchema>
 * @throws {ValidationError} When input data is invalid
 * @throws {LLMKeysApiError} When the API request fails
 */
export const updateApiKey = async (
  apiKeyId: number,
  data: UserLLMApiKeyUpdateSchema,
): Promise<UserLLMApiKeySchema> => {
  try {
    // Validate input parameters
    validateApiKeyId(apiKeyId);
    validateUpdateRequest(data);

    return await withRetry(async () => {
      const request: HollyHollyApiViewsUserLlmApiKeyViewsUpdateApiKeyRequest = {
        apiKeyId,
        userLLMApiKeyUpdateSchema: data,
      };

      return await getApiClient().hollyHollyApiViewsUserLlmApiKeyViewsUpdateApiKey(
        request,
      );
    }, "updateApiKey");
  } catch (error) {
    handleApiError(error, "Update API key");
  }
};

/**
 * Delete an LLM API key
 * @param apiKeyId - The ID of the API key to delete
 * @returns Promise<void>
 * @throws {ValidationError} When the API key ID is invalid
 * @throws {LLMKeysApiError} When the API request fails
 */
export const deleteApiKey = async (apiKeyId: number): Promise<void> => {
  try {
    // Validate input parameters
    validateApiKeyId(apiKeyId);

    return await withRetry(async () => {
      const request: HollyHollyApiViewsUserLlmApiKeyViewsDeleteApiKeyRequest = {
        apiKeyId,
      };

      return await getApiClient().hollyHollyApiViewsUserLlmApiKeyViewsDeleteApiKey(
        request,
      );
    }, "deleteApiKey");
  } catch (error) {
    handleApiError(error, "Delete API key");
  }
};
