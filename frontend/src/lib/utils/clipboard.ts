/**
 * Utility function to copy text to clipboard
 * @param text - The text to copy to clipboard
 * @returns Promise that resolves to boolean indicating success
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error("Failed to copy text: ", err);
    return false;
  }
}
