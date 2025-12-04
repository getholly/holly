/**
 * Slash Command Type Definitions
 *
 * Matches backend SlashCommand model and API schemas
 */

export interface SlashCommand {
	id: string;
	name: string;
	command_type: 'replacement' | 'function';
	description: string | null;
	replacement_text: string | null;
	function_path: string | null;
	is_system: boolean;
	is_active: boolean;
	usage_count: number;
	created_at: string;
	updated_at: string;
}

export interface SlashCommandCreate {
	name: string;
	command_type: 'replacement' | 'function';
	description?: string;
	replacement_text?: string;
	function_path?: string;
	is_active: boolean;
}

export interface SlashCommandUpdate {
	name?: string;
	command_type?: 'replacement' | 'function';
	description?: string;
	replacement_text?: string;
	function_path?: string;
	is_active?: boolean;
}
