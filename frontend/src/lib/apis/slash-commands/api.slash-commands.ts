/**
 * Slash Commands API Client
 *
 * IMPORTANT: This requires the OpenAPI client to be regenerated after the backend changes.
 * Run: npm run api:full (requires Django backend to be running)
 *
 * Once regenerated, this will use the auto-generated SlashCommandsApi client.
 */

import type {
	SlashCommand,
	SlashCommandCreate,
	SlashCommandUpdate
} from '$lib/types/slash-commands';

// TODO: Once OpenAPI client is regenerated, import these:
// import type { SlashCommandsApi } from 'holly-api';
// import { slashCommandsApi } from '$lib/apis/api.config';
// import { get } from 'svelte/store';

// Temporary implementation using fetch until OpenAPI client is regenerated
import { baseURL } from '$lib/apis/api.config';
import { getAccessToken } from '$lib/apis/api.config';

/**
 * Helper to make authenticated API calls
 */
async function fetchWithAuth<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
	const token = getAccessToken();
	const response = await fetch(`${baseURL}${endpoint}`, {
		...options,
		headers: {
			'Content-Type': 'application/json',
			Authorization: token ? `Bearer ${token}` : '',
			...options.headers
		},
		credentials: 'include'
	});

	if (!response.ok) {
		const error = await response.json().catch(() => ({ error: 'Request failed' }));
		throw new Error(error.error || `HTTP ${response.status}`);
	}

	// Handle 204 No Content
	if (response.status === 204) {
		return undefined as T;
	}

	return response.json();
}

/**
 * Get all slash commands accessible to the authenticated user.
 * Returns user's own commands + system commands.
 *
 * @param search Optional search query to filter by name or description
 * @param limit Maximum number of results (default: 50)
 * @returns Promise<SlashCommand[]> List of slash commands
 */
export async function getAllSlashCommands(
	search: string = '',
	limit: number = 50
): Promise<SlashCommand[]> {
	try {
		const params = new URLSearchParams();
		if (search) params.append('search', search);
		params.append('limit', limit.toString());

		const endpoint = `/_api/holly/slash-commands/?${params.toString()}`;
		return await fetchWithAuth<SlashCommand[]>(endpoint);
	} catch (error) {
		console.error('Error fetching slash commands:', error);
		throw error;
	}
}

/**
 * Search slash commands by name prefix (autocomplete endpoint).
 * Returns top matching commands ordered by usage count.
 *
 * @param query Search query (matched against command name prefix)
 * @param limit Maximum number of results (default: 10)
 * @returns Promise<SlashCommand[]> Matching commands
 */
export async function searchSlashCommands(
	query: string,
	limit: number = 10
): Promise<SlashCommand[]> {
	try {
		if (!query.trim()) {
			return [];
		}

		const params = new URLSearchParams();
		params.append('q', query);
		params.append('limit', limit.toString());

		const endpoint = `/_api/holly/slash-commands/search?${params.toString()}`;
		return await fetchWithAuth<SlashCommand[]>(endpoint);
	} catch (error) {
		console.error('Error searching slash commands:', error);
		throw error;
	}
}

/**
 * Get a specific slash command by ID.
 *
 * @param id The UUID of the command
 * @returns Promise<SlashCommand> The requested command
 */
export async function getSlashCommand(id: string): Promise<SlashCommand> {
	try {
		const endpoint = `/_api/holly/slash-commands/${id}`;
		return await fetchWithAuth<SlashCommand>(endpoint);
	} catch (error) {
		console.error(`Error fetching slash command ${id}:`, error);
		throw error;
	}
}

/**
 * Create a new slash command for the authenticated user.
 *
 * @param data The command configuration
 * @returns Promise<SlashCommand> The created command
 */
export async function createSlashCommand(data: SlashCommandCreate): Promise<SlashCommand> {
	try {
		const endpoint = `/_api/holly/slash-commands/`;
		return await fetchWithAuth<SlashCommand>(endpoint, {
			method: 'POST',
			body: JSON.stringify(data)
		});
	} catch (error) {
		console.error('Error creating slash command:', error);
		throw error;
	}
}

/**
 * Update an existing slash command.
 * Users can only update their own commands (not system commands).
 *
 * @param id The UUID of the command to update
 * @param data The updated command configuration
 * @returns Promise<SlashCommand> The updated command
 */
export async function updateSlashCommand(
	id: string,
	data: SlashCommandUpdate
): Promise<SlashCommand> {
	try {
		const endpoint = `/_api/holly/slash-commands/${id}`;
		return await fetchWithAuth<SlashCommand>(endpoint, {
			method: 'PUT',
			body: JSON.stringify(data)
		});
	} catch (error) {
		console.error(`Error updating slash command ${id}:`, error);
		throw error;
	}
}

/**
 * Delete (soft-delete) a slash command.
 * Users can only delete their own commands (not system commands).
 *
 * @param id The UUID of the command to delete
 * @returns Promise<void>
 */
export async function deleteSlashCommand(id: string): Promise<void> {
	try {
		const endpoint = `/_api/holly/slash-commands/${id}`;
		await fetchWithAuth<void>(endpoint, {
			method: 'DELETE'
		});
	} catch (error) {
		console.error(`Error deleting slash command ${id}:`, error);
		throw error;
	}
}
