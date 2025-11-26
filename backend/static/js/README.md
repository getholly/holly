# Token Counter Module

This module provides client-side functionality to calculate and display the running total of tokens for selected files in the file tree.

## Features

- Real-time token count updates as files are selected/deselected
- Automatic folder selection (selecting a folder selects all contained files)
- Hierarchical selection propagation (selecting all files in a folder automatically selects the folder)
- Thousand separators for better readability of large token counts

## Implementation

The token counter works by:

1. Finding all file checkboxes with the `.file-checkbox` class
2. Reading the `data-token-count` attribute from each selected file
3. Summing these values to calculate the total token count
4. Displaying the total in the `#total-token-count` element

## Integration

The script is automatically loaded in the `chat_file_tree.html` template and initializes itself when the DOM is ready.

## HTML Structure Requirements

The module expects the following HTML structure:

```html
<div id="project-tree">
  <!-- File tree content -->
  <div id="token-counter">
    Total: <span id="total-token-count">0</span> tokens
  </div>

  <!-- File checkboxes must have these attributes -->
  <input
    type="checkbox"
    class="file-checkbox"
    data-path="/path/to/file"
    data-is-dir="false"
    data-token-count="123"
  />

  <!-- Folder checkboxes must have these attributes -->
  <input
    type="checkbox"
    class="folder-checkbox"
    data-path="/path/to/folder"
    data-is-dir="true"
    data-token-count="0"
  />
</div>
```

## Testing

The module includes a test suite that can be run with:

```bash
cd /data/holly
npm test
```
