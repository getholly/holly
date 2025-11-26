import "dotenv/config";
import { themes } from "./src/lib/store/theme";

const selectedTheme = process.env.VITE_THEME || "default";

function getThemeColors(themeName: string) {
  console.log(themeName);
  return themes[themeName] || themes.default;
}

const themeColors = getThemeColors(selectedTheme);

module.exports = {
  content: [
    "./src/**/*.{html,js,svelte,ts}",
    "./node_modules/flowbite-svelte/**/*.{html,js,svelte,ts}",
    "./node_modules/flowbite-svelte-blocks/**/*.{html,js,svelte,ts}",
    "./node_modules/flowbite-svelte-svgs/**/*.{html,js,svelte,ts}",
  ],
  plugins: [
    require("flowbite/plugin"),
    require("flowbite-typography"),
    require("@tailwindcss/typography"),
  ],
  darkMode: "class",
  theme: {
    extend: {
      borderWidth: {
        "1": "1px",
      },
      colors: {
        // Theme colors using CSS variables for dynamic theming
        // Fallback values match default theme
        "theme-primary": "var(--theme-primary, #788AFB)",
        "theme-primary-dark": "var(--theme-primary-dark, #5c6cd1)",
        "theme-primary-light": "var(--theme-primary-light, #a4affc)",
        "theme-secondary": "var(--theme-secondary, #C470E8)",
        "theme-light-bg": "var(--theme-light-bg, #F2F7FF)",
        "theme-dark-bg": "var(--theme-dark-bg, #1f2937)",
        "theme-hedge": "var(--theme-hedge, #5787b8)",
        // Extended theme colors for comprehensive theming
        "theme-surface": "var(--theme-surface, #f9fafb)",
        "theme-surface-dark": "var(--theme-surface-dark, #374151)",
        "theme-border": "var(--theme-border, #e5e7eb)",
        "theme-border-dark": "var(--theme-border-dark, #4b5563)",
        "theme-text": "var(--theme-text, #111827)",
        "theme-text-secondary": "var(--theme-text-secondary, #4b5563)",
        "theme-text-muted": "var(--theme-text-muted, #6b7280)",
        "theme-text-inverse": "var(--theme-text-inverse, #ffffff)",
        primary: {
          50: "#FFF5F2",
          100: "#FFF1EE",
          200: "#FFE4DE",
          300: "#FFD5CC",
          400: "#FFBCAD",
          500: "#FE795D",
          600: "#EF562F",
          700: "#EB4F27",
          800: "#CC4522",
          900: "#A5371B",
        },
      },
    },
    fontFamily: {
      body: [
        "Inter",
        "ui-sans-serif",
        "system-ui",
        "-apple-system",
        "system-ui",
        "Segoe UI",
        "Roboto",
        "Helvetica Neue",
        "Arial",
        "Noto Sans",
        "sans-serif",
        "Apple Color Emoji",
        "Segoe UI Emoji",
        "Segoe UI Symbol",
        "Noto Color Emoji",
      ],
      mono: ["Courier New", "Roboto Mono"],
      sans: [
        "Inter",
        "ui-sans-serif",
        "system-ui",
        "-apple-system",
        "system-ui",
        "Segoe UI",
        "Roboto",
        "Helvetica Neue",
        "Arial",
        "Noto Sans",
        "sans-serif",
        "Apple Color Emoji",
        "Segoe UI Emoji",
        "Segoe UI Symbol",
        "Noto Color Emoji",
      ],
    },
  },
};
