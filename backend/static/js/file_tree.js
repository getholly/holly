/**
 * JavaScript for handling file tree interactions including token counting
 */
document.addEventListener('DOMContentLoaded', function () {
  // Initialize the file tree functionality
  initFileTree();

  // Listen for tab changes to reinitialize token counter if needed
  document.body.addEventListener('click', function (event) {
    if (event.target && event.target.id === 'diagram-tab') {
      // Delay to ensure DOM is updated
      setTimeout(function () {
        initFileTree();
      }, 200);
    }
  });
});

/**
 * Initialize the file tree functionality including token counter
 */
function initFileTree() {
  // Debug logging function
  function debugLog(message, data) {
    if (window.localStorage.getItem('debug_token_counter') === 'true') {
      console.log(`[Token Counter] ${message}`, data || '');
    }
  }

  // Initialize token data from file tree - update to use Alpine store
  function initializeTokenData() {
    debugLog('Initializing token data');

    if (window.Alpine && Alpine.store('tokenCounter')) {
      const tokenStore = Alpine.store('tokenCounter');

      // Reset the store
      tokenStore.totalTokens = 0;
      tokenStore.tokenCounts = {};
      tokenStore.selectedFiles.clear();

      // Gather data from checkboxes
      const checkboxes = document.querySelectorAll(
        '.file-checkbox, .folder-checkbox',
      );
      debugLog(`Found ${checkboxes.length} checkboxes`);

      checkboxes.forEach((checkbox) => {
        const path = checkbox.dataset.path;
        const tokenCount = parseInt(checkbox.dataset.tokenCount || 0, 10);

        debugLog(`Item: ${path}, Tokens: ${tokenCount}`);
        tokenStore.tokenCounts[path] = tokenCount;

        if (checkbox.checked) {
          tokenStore.selectedFiles.add(path);
          tokenStore.totalTokens += tokenCount;
        }
      });

      // Recalculate total after initialization
      tokenStore.recalculateTotal();
    }
  }
  function handleCheckboxChange(event) {
    console.log('token_counter2-file_tree.js');
    const checkbox = event.target;
    const path = checkbox.dataset.path;
    const tokenCount = parseInt(checkbox.dataset.tokenCount || 0, 10);
    const isDir = checkbox.dataset.isDir === 'true';

    debugLog(
      `Checkbox change: ${path}, isChecked: ${checkbox.checked}, tokenCount: ${tokenCount}`,
    );

    if (window.Alpine && Alpine.store('tokenCounter')) {
      const tokenStore = Alpine.store('tokenCounter');

      // Update selected files and token count
      if (checkbox.checked) {
        tokenStore.addFile(path, tokenCount);

        // If it's a directory, select all its children
        if (isDir) {
          const detailsElement = checkbox.closest('details');
          if (detailsElement) {
            const childCheckboxes = detailsElement.querySelectorAll(
              '.file-checkbox, .folder-checkbox',
            );
            debugLog(`Found ${childCheckboxes.length} children in directory`);

            childCheckboxes.forEach((childCheckbox) => {
              if (childCheckbox !== checkbox && !childCheckbox.checked) {
                childCheckbox.checked = true;
                const childPath = childCheckbox.dataset.path;
                const childTokenCount = parseInt(
                  childCheckbox.dataset.tokenCount || 0,
                  10,
                );

                if (!tokenStore.selectedFiles.has(childPath)) {
                  tokenStore.addFile(childPath, childTokenCount);
                }
              }
            });
          }
        }
      } else {
        tokenStore.removeFile(path);

        // If it's a directory, deselect all its children
        if (isDir) {
          const detailsElement = checkbox.closest('details');
          if (detailsElement) {
            const childCheckboxes = detailsElement.querySelectorAll(
              '.file-checkbox, .folder-checkbox',
            );
            debugLog(
              `Found ${childCheckboxes.length} children in directory to deselect`,
            );

            childCheckboxes.forEach((childCheckbox) => {
              if (childCheckbox !== checkbox && childCheckbox.checked) {
                childCheckbox.checked = false;
                const childPath = childCheckbox.dataset.path;
                tokenStore.removeFile(childPath);
              }
            });
          }
        }
      }

      // Recalculate the total
      tokenStore.recalculateTotal();
    }
  }
  // Add event listeners to checkboxes
  function addCheckboxEventListeners() {
    const checkboxes = document.querySelectorAll(
      '.file-checkbox, .folder-checkbox',
    );
    debugLog(`Adding event listeners to ${checkboxes.length} checkboxes`);

    checkboxes.forEach((checkbox) => {
      // Remove any existing listeners to prevent duplicates
      checkbox.removeEventListener('change', handleCheckboxChange);
      // Add the change event listener
      checkbox.addEventListener('change', handleCheckboxChange);
    });
  }

  // Enable debug mode with localStorage
  // To enable: localStorage.setItem('debug_token_counter', 'true')
  // To disable: localStorage.removeItem('debug_token_counter')
  debugLog('Token counter initialized with debug mode');

  // Initialize token data and add event listeners
  initializeTokenData();
  addCheckboxEventListeners();

  // Re-initialize when the tree is updated via HTMX
  document.body.addEventListener('htmx:afterSwap', function (event) {
    if (event.detail.target.id === 'project-tree') {
      debugLog('Tree updated via HTMX, reinitializing');
      initializeTokenData();
      addCheckboxEventListeners();
    }
  });

  // Also listen for fileTreeUpdated event from repo-analysis.js
  document.addEventListener('fileTreeUpdated', function () {
    debugLog('File tree updated from repo-analysis, reinitializing');
    setTimeout(function () {
      initializeTokenData();
      addCheckboxEventListeners();
    }, 100);
  });
}

// Export for testing purposes
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { initFileTree };
}
