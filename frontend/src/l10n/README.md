# Project Localization Guide

This guide provides the necessary steps to run the localization process for the project. The goal is to update the translations and generate new language files (e.g., de.json, fr.json, etc.) using a language translation model.

## Steps to Run Localization

### 1. Navigate to the Source Directory

First, open your terminal and navigate to the src directory:

```bash
cd src
```

### 2. Copy en.json to translations.json

In the src directory, you need to copy the en.json file from the l10n folder to translations.json in order to update it with new translations:

```bash
copy .\l10n\en.json .\translations.json
```

(Note: If you are on macOS or Linux, use cp instead of copy)

### 3. Run the Translation Processor

Next, run the processor.js script using Node.js to update the translations.json file. This script processes your translations:

```bash
node ..\tools\processor.js .
```

This will update translations.json with the latest translation keys and values based on the script's logic.

### 4. Copy Updated Translations Back to en.json

After processing the translations, copy the updated translations.json back to l10n\en.json to ensure the English translations are updated:

```bash
copy .\translations.json .\l10n\en.json
```

(Note: Use cp on macOS or Linux)

### 5. Generate Translations for Other Languages

To generate language-specific JSON files (e.g., de.json for German, fr.json for French, etc.), take the updated en.json file and use a language translation Large Language Model (LLM) to translate it. This process can vary depending on the translation tool you use.

For example:

- Use your preferred LLM to translate en.json to de.json (German), fr.json (French), etc.
- Save the translated files in the l10n folder with the appropriate language codes (e.g., de.json, fr.json, etc.).

### 6. Register New Languages

Once you've generated the new translation files, make sure to add them to the i18n.ts file

### 7. Update LanguageChooser.svelte

Finally, update the LanguageChooser.svelte component to include the new
languages in the languages array.
