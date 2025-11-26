export const capitalise = (str: string, lower: boolean = false): string =>
  (lower ? str.toLowerCase() : str)
    .replace(/(?:^|\s|["'([{])+\S/g, (match) => match.toUpperCase())
    .replace("_", " ");

export function convertToValidHtmlAttribute(input: string): string {
  // Step 1: Convert to lowercase and trim whitespace
  let result = input.toLowerCase().trim();

  // Step 2: Replace spaces and other invalid characters with hyphens
  result = result.replace(/[^a-z0-9\-_:.]/g, "-");

  // Step 3: Replace multiple consecutive hyphens with a single hyphen
  result = result.replace(/-+/g, "-");

  // Step 4: Remove leading and trailing hyphens
  result = result.replace(/^-+|-+$/g, "");

  // Step 5: Ensure it starts with a letter if it's not empty
  if (result.length > 0 && !result.match(/^[a-z]/)) {
    result = "id-" + result;
  }

  // Step 6: If the string is empty after all replacements, provide a default
  if (result.length === 0) {
    result = "default-id";
  }

  return result;
}

export function removeSurroundingChar(str: string, charToRemove: string) {
  // 1. Check if the input is a string and has the minimum length (4 for **)
  if (str.length < 4) {
    return str; // Return original if not a string or too short
  }

  if (str.startsWith(charToRemove) && str.endsWith(charToRemove)) {
    return str.slice(charToRemove.length, -1 * charToRemove.length);
  } else {
    return str;
  }
}
