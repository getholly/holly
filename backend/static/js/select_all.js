/**
 * JavaScript for handling the "ALL" checkbox to select or deselect all files and directories
 */
document.addEventListener('DOMContentLoaded', function () {
  initSelectAll();

  // Re-initialize when the tree is updated via HTMX
  document.body.addEventListener('htmx:afterSwap', function (event) {
    if (event.detail.target.id === 'project-tree') {
      initSelectAll();
      selectAllFiles();
    }
  });

  // Also listen for fileTreeUpdated event
  document.addEventListener('fileTreeUpdated', function () {
    setTimeout(function () {
      initSelectAll();
      selectAllFiles();
    }, 100);
  });
  setTimeout(selectAllFiles, 300);
});

/**
 * Function to select all files by default
 */
function selectAllFiles() {
  const selectAllCheckbox = document.getElementById('select-all-checkbox');
  if (selectAllCheckbox && !selectAllCheckbox.checked) {
    selectAllCheckbox.checked = true;

    // Manually trigger the change handler to select all files
    handleSelectAllChange({ target: selectAllCheckbox });

    // If needed, dispatch a custom event to notify other components
    document.dispatchEvent(
      new CustomEvent('allFilesSelected', {
        detail: { selectedByDefault: true },
      }),
    );
  }
}

/**
 * Initialize the select all functionality
 */
function initSelectAll() {
  const selectAllCheckbox = document.getElementById('select-all-checkbox');
  if (!selectAllCheckbox) return;

  // Initialize selectAll checkbox state based on current selection
  updateSelectAllState();

  // Add event listener to the select all checkbox
  selectAllCheckbox.removeEventListener('change', handleSelectAllChange);
  selectAllCheckbox.addEventListener('change', handleSelectAllChange);

  // Add event listeners to all file/folder checkboxes to update selectAll state
  const fileCheckboxes = document.querySelectorAll(
    '.file-checkbox, .folder-checkbox',
  );
  fileCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener('change', updateSelectAllState);
  });
}

/**
 * Handle the change event of the select all checkbox
 * @param {Event} event - The change event
 */
function handleSelectAllChange(event) {
  const isChecked = event.target.checked;
  const allCheckboxes = document.querySelectorAll(
    '.file-checkbox, .folder-checkbox',
  );

  // Update all checkboxes
  allCheckboxes.forEach((checkbox) => {
    // Only trigger change event if the checkbox state actually changes
    if (checkbox.checked !== isChecked) {
      checkbox.checked = isChecked;

      // Dispatch a change event to trigger the token counter update
      const changeEvent = new Event('change', { bubbles: true });
      checkbox.dispatchEvent(changeEvent);
    }
  });
}

/**
 * Update the state of the select all checkbox based on the current selection
 */
function updateSelectAllState() {
  const selectAllCheckbox = document.getElementById('select-all-checkbox');
  if (!selectAllCheckbox) return;

  const allCheckboxes = document.querySelectorAll(
    '.file-checkbox, .folder-checkbox',
  );
  const checkedCount = document.querySelectorAll(
    '.file-checkbox:checked, .folder-checkbox:checked',
  ).length;

  if (allCheckboxes.length === 0) {
    selectAllCheckbox.checked = false;
    selectAllCheckbox.indeterminate = false;
  } else if (checkedCount === 0) {
    selectAllCheckbox.checked = false;
    selectAllCheckbox.indeterminate = false;
  } else if (checkedCount === allCheckboxes.length) {
    selectAllCheckbox.checked = true;
    selectAllCheckbox.indeterminate = false;
  } else {
    selectAllCheckbox.checked = false;
    selectAllCheckbox.indeterminate = true;
  }
}

// Export for testing purposes
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    initSelectAll,
    handleSelectAllChange,
    updateSelectAllState,
  };
}
