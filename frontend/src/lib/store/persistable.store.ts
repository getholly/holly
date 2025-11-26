import { writable, type Writable } from "svelte/store";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

export function persistableStore<T>(key: string, initialValue: T): Writable<T> {
  let data: T;

  // Check if running in the browser and use localStorage if available
  if (isBrowser()) {
    const storedValue = localStorage.getItem(key);
    if (
      storedValue !== undefined &&
      storedValue !== null &&
      storedValue !== "undefined"
    ) {
      data = storedValue ? JSON.parse(storedValue) : initialValue;
    } else {
      data = initialValue;
    }
  } else {
    // Fallback to initial value if not in the browser
    data = initialValue;
  }

  const store = writable(data);

  // Only subscribe to changes if on the client
  if (isBrowser()) {
    store.subscribe((currentValue: T) => {
      localStorage.setItem(key, JSON.stringify(currentValue));
    });
  }

  return store;
}
