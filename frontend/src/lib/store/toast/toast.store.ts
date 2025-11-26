import { writable } from "svelte/store";

export interface Toast {
  id: number;
  message: string;
  type: "success" | "error" | "warning" | "info";
  duration: number;
}

interface ToastStore {
  subscribe: (callback: (value: Toast[]) => void) => () => void;
  addToast: (
    message: string,
    type?: Toast["type"],
    duration?: number,
  ) => number;
  removeToast: (id: number) => void;
}

const createToastStore = (): ToastStore => {
  const { subscribe, update } = writable<Toast[]>([]);

  const removeToast = (id: number): void => {
    update((toasts) => toasts.filter((t) => t.id !== id));
  };

  const addToast = (
    message: string,
    type: Toast["type"] = "success",
    duration = 3000,
  ): number => {
    const id = Date.now();
    update((toasts) => [...toasts, { id, message, type, duration }]);

    // Set a timer to remove the toast after its duration
    setTimeout(() => {
      removeToast(id);
    }, duration);

    return id;
  };

  return {
    subscribe,
    addToast,
    removeToast,
  };
};

export const toastStore = createToastStore();

export function showToast(
  message: string,
  type: Toast["type"] = "success",
  duration = 2000,
): number {
  return toastStore.addToast(message, type, duration);
}
