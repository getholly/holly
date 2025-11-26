/**
 * File Extension Filter Module
 *
 * This module provides functionality for filtering files in the file tree by extension
 * and showing token counts per extension.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize the file extension filter
  initFileExtensionFilter();
});

/**
 * Initialize the file extension filter functionality
 */
function initFileExtensionFilter() {
  // DOM elements
  const filterButton = document.querySelector('#project-tree button');
  const modal = document.getElementById('file-extension-filter-modal');
  const closeModalButton = document.getElementById('close-filter-modal');
  const extensionListElement = document.getElementById('extension-list');
  const selectedTokenCountElement = document.getElementById(
    'selected-extensions-token-count',
  );
  const selectAllButton = document.getElementById('select-all-extensions');
  const clearAllButton = document.getElementById('clear-all-extensions');
  const applyFilterButton = document.getElementById('apply-filter');

  // Store extension data
  let extensionData = [];
  let selectedExtensions = [];

  // Event listeners
  if (filterButton) {
    filterButton.addEventListener('click', openFilterModal);
  }

  if (closeModalButton) {
    closeModalButton.addEventListener('click', closeFilterModal);
  }

  if (selectAllButton) {
    selectAllButton.addEventListener('click', selectAllExtensions);
  }

  if (clearAllButton) {
    clearAllButton.addEventListener('click', clearAllExtensions);
  }

  if (applyFilterButton) {
    applyFilterButton.addEventListener('click', applyFilter);
  }

  // Close modal when clicking outside
  window.addEventListener('click', (event) => {
    if (event.target === modal) {
      closeFilterModal();
    }
  });

  /**
   * Open the filter modal and populate extension data
   */
  function openFilterModal() {
    // Collect extension data
    collectExtensionData();

    // Update modal with extension data
    updateExtensionList();

    // Set initial selected extensions from current checked state
    updateSelectedExtensions();

    // Update token count
    updateSelectedTokenCount();

    // Show modal
    modal.classList.remove('hidden');
  }

  /**
   * Close the filter modal
   */
  function closeFilterModal() {
    modal.classList.add('hidden');
  }

  /**
   * Collect data on file extensions from all files in the tree
   */
  function collectExtensionData() {
    // Reset extension data
    extensionData = [];

    // Get all file checkboxes
    const fileCheckboxes = document.querySelectorAll('.file-checkbox');

    // Temporary object to store extension info
    const extensionsInfo = {};

    // Process each file
    fileCheckboxes.forEach((checkbox) => {
      const filePath = checkbox.getAttribute('data-path');
      const tokenCount =
        parseInt(checkbox.getAttribute('data-token-count')) || 0;

      // Extract extension
      let extension = extractExtension(filePath);

      // If extension doesn't exist in our collection, add it
      if (!extensionsInfo[extension]) {
        extensionsInfo[extension] = {
          extension: extension,
          fileCount: 0,
          tokenCount: 0,
          files: [],
        };
      }

      // Update extension info
      extensionsInfo[extension].fileCount++;
      extensionsInfo[extension].tokenCount += tokenCount;
      extensionsInfo[extension].files.push({
        path: filePath,
        tokenCount: tokenCount,
      });
    });

    // Convert object to array and sort by extension
    extensionData = Object.values(extensionsInfo).sort((a, b) =>
      a.extension.localeCompare(b.extension),
    );
  }

  /**
   * Extract file extension from a path
   * @param {string} filePath - Path to the file
   * @returns {string} - The file extension with dot prefix (e.g., ".js")
   */
  function extractExtension(filePath) {
    const fileName = filePath.split('/').pop();
    const lastDotIndex = fileName.lastIndexOf('.');

    if (lastDotIndex === -1) {
      return '(no extension)';
    }

    return fileName.slice(lastDotIndex);
  }

  /**
   * Get readable extension name
   * @param {string} extension - The file extension with dot prefix
   * @returns {string} - Human readable extension name
   */
  function getReadableExtension(extension) {
    if (extension === '(no extension)') {
      return '(no extension)';
    }

    // Remove the dot and get the common names for extensions
    const ext = extension.slice(1);

    const extensionNames = {
      js: 'JavaScript',
      py: 'Python',
      html: 'HTML',
      css: 'CSS',
      md: 'Markdown',
      json: 'JSON',
      txt: 'Text',
      csv: 'CSV',
      yml: 'YAML',
      yaml: 'YAML',
      sh: 'Shell',
      jsx: 'React JSX',
      tsx: 'React TSX',
      ts: 'TypeScript',
      java: 'Java',
      c: 'C',
      cpp: 'C++',
      h: 'C Header',
      hpp: 'C++ Header',
      rb: 'Ruby',
      php: 'PHP',
      go: 'Go',
      rs: 'Rust',
      swift: 'Swift',
      kt: 'Kotlin',
      dart: 'Dart',
      sql: 'SQL',
    };

    return extensionNames[ext]
      ? `${extensionNames[ext]} (${extension})`
      : extension;
  }

  /**
   * Update the extension list in the modal
   */
  function updateExtensionList() {
    // Clear current list
    extensionListElement.innerHTML = '';

    // Add each extension to the list
    extensionData.forEach((extInfo, index) => {
      const readableExtension = getReadableExtension(extInfo.extension);

      const listItem = document.createElement('li');
      listItem.className =
        'p-2 text-gray-700 dark:text-gray-100 bg-gray-200 dark:bg-gray-600 dark:hover:bg-gray-700';
      listItem.innerHTML = `
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="checkbox"
                 class="extension-checkbox fb-checkbox"
                 data-extension="${extInfo.extension}"
                 data-index="${index}">
          <span class="flex-grow text-sm">
            ${readableExtension} - ${extInfo.fileCount}(f), ${extInfo.tokenCount.toLocaleString()}(tok)
          </span>
        </label>
      `;

      extensionListElement.appendChild(listItem);
    });

    // Add event listeners to checkboxes
    const extensionCheckboxes = document.querySelectorAll(
      '.extension-checkbox',
    );
    extensionCheckboxes.forEach((checkbox) => {
      checkbox.addEventListener('change', () => {
        updateSelectedExtensions();
        updateSelectedTokenCount();
      });
    });
  }

  /**
   * Update the selected extensions array based on checkbox state
   */
  function updateSelectedExtensions() {
    selectedExtensions = [];

    const extensionCheckboxes = document.querySelectorAll(
      '.extension-checkbox',
    );
    extensionCheckboxes.forEach((checkbox) => {
      if (checkbox.checked) {
        const index = parseInt(checkbox.getAttribute('data-index'));
        selectedExtensions.push(extensionData[index]);
      }
    });
  }

  /**
   * Update the token count display for selected extensions
   */
  function updateSelectedTokenCount() {
    let totalTokens = 0;

    selectedExtensions.forEach((extInfo) => {
      totalTokens += extInfo.tokenCount;
    });

    selectedTokenCountElement.textContent = totalTokens.toLocaleString();
  }

  /**
   * Select all extensions
   */
  function selectAllExtensions() {
    const extensionCheckboxes = document.querySelectorAll(
      '.extension-checkbox',
    );
    extensionCheckboxes.forEach((checkbox) => {
      checkbox.checked = true;
    });

    updateSelectedExtensions();
    updateSelectedTokenCount();
  }

  /**
   * Clear all extension selections
   */
  function clearAllExtensions() {
    const extensionCheckboxes = document.querySelectorAll(
      '.extension-checkbox',
    );
    extensionCheckboxes.forEach((checkbox) => {
      checkbox.checked = false;
    });

    updateSelectedExtensions();
    updateSelectedTokenCount();
  }

  /**
   * Apply the filter to the file tree
   */
  function applyFilter() {
    // Get all file checkboxes
    const fileCheckboxes = document.querySelectorAll('.file-checkbox');

    // Create array of selected extensions
    const selectedExtensionNames = selectedExtensions.map(
      (ext) => ext.extension,
    );

    // Filter files
    fileCheckboxes.forEach((checkbox) => {
      const filePath = checkbox.getAttribute('data-path');
      const extension = extractExtension(filePath);

      // Check or uncheck based on if the extension is selected
      checkbox.checked = selectedExtensionNames.includes(extension);
    });

    // Update folder checkboxes based on file selections
    updateFolderCheckboxes();

    // Update the total token count using the Alpine store
    if (window.Alpine && Alpine.store('tokenCounter')) {
      Alpine.store('tokenCounter').recalculateTotal();
    }

    // Close the modal
    closeFilterModal();
  }

  /**
   * Update folder checkboxes based on file selections
   */
  function updateFolderCheckboxes() {
    // Get all folder checkboxes
    const folderCheckboxes = document.querySelectorAll('.folder-checkbox');

    // Process each folder
    folderCheckboxes.forEach((folderCheckbox) => {
      const details = folderCheckbox.closest('details');
      if (details) {
        // Find child file checkboxes
        const childFiles = details.querySelectorAll('.file-checkbox');

        // Check if any files are checked
        const anyChecked = Array.from(childFiles).some((file) => file.checked);

        // Check if all files are checked
        const allChecked =
          childFiles.length > 0 &&
          Array.from(childFiles).every((file) => file.checked);

        // Update folder checkbox
        if (allChecked) {
          folderCheckbox.checked = true;
          folderCheckbox.indeterminate = false;
        } else if (anyChecked) {
          folderCheckbox.checked = false;
          folderCheckbox.indeterminate = true;
        } else {
          folderCheckbox.checked = false;
          folderCheckbox.indeterminate = false;
        }
      }
    });
  }
}

// Export for testing purposes
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { initFileExtensionFilter };
}
