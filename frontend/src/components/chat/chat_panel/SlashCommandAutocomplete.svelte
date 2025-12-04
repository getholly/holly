<script lang="ts">
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { debounce } from '$lib/utils/debounce';
	import { searchSlashCommands } from '$lib/apis/slash-commands/api.slash-commands';
	import type { SlashCommand } from '$lib/types/slash-commands';

	export let query: string = '';
	export let isVisible: boolean = false;
	export let textareaElement: HTMLTextAreaElement | null = null;

	let suggestions: SlashCommand[] = [];
	let selectedIndex: number = 0;
	let isLoading: boolean = false;
	let dropdownElement: HTMLDivElement | null = null;

	const dispatch = createEventDispatcher<{
		select: { command: SlashCommand };
		close: void;
	}>();

	/**
	 * Fetch slash command suggestions from the API
	 */
	async function fetchSuggestions(searchQuery: string): Promise<void> {
		if (!searchQuery) {
			suggestions = [];
			return;
		}

		isLoading = true;
		try {
			const results = await searchSlashCommands(searchQuery);
			suggestions = results.filter((cmd) => cmd.is_active);
			selectedIndex = 0;
		} catch (err) {
			console.error('Autocomplete fetch error:', err);
			suggestions = [];
		} finally {
			isLoading = false;
		}
	}

	// Debounced version of fetchSuggestions (200ms delay)
	const debouncedFetch = debounce(fetchSuggestions, 200);

	/**
	 * Reactive statement to fetch suggestions when query changes
	 */
	$: if (isVisible && query) {
		debouncedFetch(query.toLowerCase().trim());
	} else if (!isVisible) {
		suggestions = [];
	}

	/**
	 * Handle keyboard navigation within the autocomplete dropdown
	 */
	export function handleKeyNavigation(event: KeyboardEvent): boolean {
		if (!isVisible || suggestions.length === 0) return false;

		switch (event.key) {
			case 'ArrowDown':
				event.preventDefault();
				selectedIndex = (selectedIndex + 1) % suggestions.length;
				scrollSelectedIntoView();
				return true;

			case 'ArrowUp':
				event.preventDefault();
				selectedIndex = selectedIndex === 0 ? suggestions.length - 1 : selectedIndex - 1;
				scrollSelectedIntoView();
				return true;

			case 'Enter':
			case 'Tab':
				event.preventDefault();
				dispatch('select', { command: suggestions[selectedIndex] });
				return true;

			case 'Escape':
				event.preventDefault();
				dispatch('close');
				return true;

			default:
				return false;
		}
	}

	/**
	 * Scroll the selected item into view
	 */
	function scrollSelectedIntoView(): void {
		if (!dropdownElement) return;

		const selectedElement = dropdownElement.querySelector(`[data-index="${selectedIndex}"]`);
		if (selectedElement) {
			selectedElement.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
		}
	}

	/**
	 * Calculate and update the dropdown position relative to the textarea
	 */
	let dropdownStyle = '';
	function updatePosition(): void {
		if (!textareaElement || !dropdownElement) return;

		const textareaRect = textareaElement.getBoundingClientRect();

		// Position dropdown above the textarea
		dropdownStyle = `
			left: ${textareaRect.left}px;
			width: ${textareaRect.width}px;
			bottom: ${window.innerHeight - textareaRect.top + 8}px;
		`;
	}

	/**
	 * Update position when visibility changes or when suggestions appear
	 */
	$: if (isVisible && suggestions.length > 0 && textareaElement) {
		// Use setTimeout to ensure DOM has updated
		setTimeout(updatePosition, 0);
	}

	// Update position on window resize
	onMount(() => {
		window.addEventListener('resize', updatePosition);
	});

	onDestroy(() => {
		window.removeEventListener('resize', updatePosition);
	});
</script>

{#if isVisible && suggestions.length > 0}
	<div
		bind:this={dropdownElement}
		class="fixed z-50 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 max-h-64 overflow-y-auto"
		style={dropdownStyle}
		role="listbox"
		aria-label="Slash command suggestions"
	>
		<ul class="py-2">
			{#each suggestions as command, index (command.id)}
				<li
					data-index={index}
					class="px-4 py-2 cursor-pointer transition-colors {index === selectedIndex
						? 'bg-blue-100 dark:bg-blue-900/30'
						: 'hover:bg-gray-100 dark:hover:bg-gray-700'}"
					role="option"
					aria-selected={index === selectedIndex}
					on:click={() => dispatch('select', { command })}
					on:mouseenter={() => {
						selectedIndex = index;
					}}
				>
					<div class="flex items-start gap-3">
						<span
							class="text-blue-600 dark:text-blue-400 font-mono text-sm font-semibold min-w-fit"
						>
							/{command.name}
						</span>
						{#if command.description}
							<p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-1">
								{command.description}
							</p>
						{/if}
						{#if command.is_system}
							<span
								class="ml-auto text-xs bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 px-2 py-0.5 rounded"
							>
								System
							</span>
						{/if}
					</div>
				</li>
			{/each}
		</ul>
	</div>
{:else if isVisible && isLoading}
	<div
		class="fixed z-50 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 px-4 py-3"
		style={dropdownStyle}
	>
		<p class="text-sm text-gray-500 dark:text-gray-400">Searching commands...</p>
	</div>
{/if}

<style>
	.line-clamp-1 {
		overflow: hidden;
		display: -webkit-box;
		-webkit-box-orient: vertical;
		-webkit-line-clamp: 1;
	}
</style>
