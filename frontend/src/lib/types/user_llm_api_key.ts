export interface UserLLMApiKeySchema {
  id: number;
  llm_id: number;
  llm_name: string;
  api_key: string; // Masked or partial e.g., "**********key1"
  created_at: string; // ISO string format
  updated_at: string; // ISO string format
}

export interface UserLLMApiKeyCreateSchema {
  llm_id: number;
  api_key: string;
}

export interface UserLLMApiKeyUpdateSchema {
  api_key: string;
}

// This could also include other related types, for example,
// a combined type for display in the UI if needed.
export interface LLMApiKeyDisplay extends UserLLMApiKeySchema {
  // any additional UI-specific fields can go here
  isEditing?: boolean;
  currentInputValue?: string;
}

export interface SupportedLLMSchema {
  id: number;
  name: string;
  // any other properties that might be relevant from your LLMSchema
}
