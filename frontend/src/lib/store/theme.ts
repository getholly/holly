// src/lib/config/theme.ts
// OSS: Fixed default theme configuration
// For customizable themes, use the Enterprise Edition

export interface ThemeAsset {
  src: string;
  alt: string;
  class?: string;
  link?: string;
}

export interface ThemeMeta {
  title: string;
  description: string;
  image: string;
}

export interface Theme {
  primaryColor: string;
  secondaryColor: string;
  hedgeColor: string;
  darkbgColor: string;
  lightbgColor: string;
  disabledRoutes: string[];
  companyName: string;
  openRoutes: string[];
  avatar: ThemeAsset;
  logo: ThemeAsset;
  logoDark: ThemeAsset;
  icon: ThemeAsset;
  authBackgroundClass: string;
  background: string;
  favicon: string;
  title: string;
  defaultColour: string;
  contactEmail: string;
  mainRoute: string;
  poweredByLogo: ThemeAsset;
  meta: ThemeMeta;
}

// Default theme configuration - centralized for easy adjustment
export const defaultTheme: Theme = {
  primaryColor: "#174c83",
  secondaryColor: "#3e3aa7",
  hedgeColor: "#5787b8",
  darkbgColor: "#1E2939",
  lightbgColor: "#FFFFFF",
  disabledRoutes: [],
  companyName: "Imperial AI Limited",
  openRoutes: ["/login", "/register", "/verify-email"],
  avatar: { src: "/gaia/ling.webp", alt: "Avatar" },
  logo: { src: "/img/holly-logo-dark.png", alt: "holly logo" },
  logoDark: { src: "/img/holly-logo.png", alt: "holly logo dark" },
  icon: { src: "/img/holly-icon.png", alt: "holly icon" },
  authBackgroundClass: "",
  background: "githubme/background.jpg",
  favicon: "/img/holly-icon-small.png",
  title: "githubme.com",
  defaultColour: "blue",
  contactEmail: "ling@githubme.com",
  mainRoute: "/sse-chat",
  poweredByLogo: {
    src: "/img/techarge-logo-white.png",
    alt: "Imperial AI Logo",
    class: "w-24",
    link: "https://www.techarge.co.uk",
  },
  meta: {
    title: "githubme",
    description: "githubme",
    image: "/githubme/Logo.png",
  },
};

// For backwards compatibility with existing code that imports `themes`
export const themes = {
  default: defaultTheme,
};
