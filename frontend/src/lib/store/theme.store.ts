// src/store/theme.store.ts
// OSS: Fixed theme store - uses default theme only
// For customizable themes, use the Enterprise Edition

import { writable } from "svelte/store";
import { defaultTheme, themes, type Theme } from "$lib/store/theme";

// OSS uses fixed default theme
export const selectedTheme = writable<Theme>(defaultTheme);

// Export for backwards compatibility
export { themes, defaultTheme, type Theme };
