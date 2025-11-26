// see: https://github.com/kaisermann/svelte-i18n/blob/main/docs/Locale.md#loading
import { getLocaleFromNavigator, init, locale, register } from "svelte-i18n";

// async loading
// register("en", () => import("./en.json"))
register("en-GB", () => import("./en.json")); // Brit english - Default
register("en-US", () => import("./us.json"));
register("fr", () => import("./fr.json"));
register("fr-CH", () => import("./fr.json")); // swiss french
register("de-CH", () => import("./gsw.json")); // swiss german
register("de", () => import("./de.json")); // german
register("ru", () => import("./ru.json")); // russian
register("es", () => import("./es.json")); // spanish
register("zh", () => import("./zh.json")); // chinese

locale.set(navigator.language || "en-GB");

init({
  fallbackLocale: "en-GB",
  initialLocale: getLocaleFromNavigator(),
});
