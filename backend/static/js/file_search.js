/**
 * File Search Module
 *
 * This module provides functionality for filtering files in the file tree by filename.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize the file search functionality
  initFileSearch();
});

/**
 * Initialize the file search functionality
 */
function initFileSearch() {
  // DOM elements
  const searchInput = document.getElementById('file-search');
  if (!searchInput) return;

  // Store original visibility state
  let originalVisibility = new Map();

  // Add event listener for input changes
  searchInput.addEventListener('input', filterFileTree);

  /**
   * Filter the file tree based on search input
   */
  function filterFileTree() {
    const searchTerm = searchInput.value.toLowerCase().trim();

    // Get all list items in the file tree
    const fileItems = document.querySelectorAll('#project-tree li');

    // First time initialization of original visibility
    if (originalVisibility.size === 0) {
      fileItems.forEach((item, index) => {
        originalVisibility.set(index, item.style.display);
      });
    }

    // Reset visibility before new filtering if search is empty
    if (searchTerm === '') {
      fileItems.forEach((item, index) => {
        item.style.display = originalVisibility.get(index) || '';

        // Ensure parent directories are visible
        const parentDetails = item.closest('details');
        if (parentDetails) {
          parentDetails.open = false;
        }
      });
      return;
    }

    // For each list item...
    fileItems.forEach((item) => {
      const fileName = getFileNameFromItem(item);

      if (fileName && fileName.toLowerCase().includes(searchTerm)) {
        // Show matching items
        item.style.display = '';

        // Open all parent directories
        let parent = item.parentElement;
        while (parent) {
          const parentDetails = parent.closest('details');
          if (parentDetails) {
            parentDetails.open = true;
            parent = parentDetails.parentElement;
          } else {
            break;
          }
        }
      } else if (hasMatchingChild(item, searchTerm)) {
        // If it's a directory with matching children, show it
        item.style.display = '';

        // Open the directory
        const details = item.querySelector('details');
        if (details) {
          details.open = true;
        }
      } else {
        // Hide non-matching items
        item.style.display = 'none';
      }
    });
  }

  /**
   * Extract filename from a list item
   * @param {HTMLElement} item - List item element
   * @returns {string|null} - Filename or null if not found
   */
  function getFileNameFromItem(item) {
    // For files
    const fileSpan = item.querySelector('div > span');
    if (fileSpan) {
      return fileSpan.textContent.trim();
    }

    // For directories
    const summaryText = item.querySelector('summary');
    if (summaryText) {
      // Extract directory name from the summary text
      const text = summaryText.textContent.trim();
      // Find the directory name (between 📁 and tokens)
      const match = text.match(/📁\s+([^(]+)/);
      return match ? match[1].trim() : null;
    }

    return null;
  }

  /**
   * Check if an item has any children matching the search term
   * @param {HTMLElement} item - The list item to check
   * @param {string} searchTerm - The search term
   * @returns {boolean} - True if has matching children
   */
  function hasMatchingChild(item, searchTerm) {
    const details = item.querySelector('details');
    if (!details) return false;

    const childItems = details.querySelectorAll('li');
    for (const childItem of childItems) {
      const childName = getFileNameFromItem(childItem);
      if (childName && childName.toLowerCase().includes(searchTerm)) {
        return true;
      }

      // Recursively check nested directories
      if (hasMatchingChild(childItem, searchTerm)) {
        return true;
      }
    }

    return false;
  }
}

// Export for testing purposes
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { initFileSearch };
}

// Make function globally available
window.initFileSearch = initFileSearch;
