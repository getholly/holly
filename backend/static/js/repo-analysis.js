/**
 * Repository analysis page handling.
 *
 * This module handles updating the repository analysis page
 * as background tasks complete.
 */

document.addEventListener('DOMContentLoaded', function () {
  // Check if we're on the repo analysis page and have a task ID
  const taskIdElement = document.getElementById('bg-task-id');
  if (!taskIdElement) return;

  const taskId = taskIdElement.dataset.taskId;
  if (!taskId) return;

  // Elements that will be updated
  const fileTreeContainer = document.getElementById('file-tree-container');
  const fileTreeSpinner = document.getElementById('file-tree-spinner');
  const infoPanel = document.getElementById('info-panel');
  const infoPanelSpinner = document.getElementById('info-panel-spinner');

  // Start polling for the repository analysis task
  const endpoint = `/_analysis-data/${taskId}/`;

  window.taskManager.startPolling(
    taskId,
    endpoint,
    // onSuccess - task completed successfully
    function (data) {
      console.log('Repository analysis completed:', data);

      // Update file tree
      if (fileTreeContainer && fileTreeSpinner && data.file_tree) {
        updateFileTree(data.file_tree);
        fileTreeSpinner.classList.add('hidden');
        fileTreeContainer.classList.remove('hidden');
      }

      // Update info panel metrics
      if (infoPanel && infoPanelSpinner) {
        updateInfoPanel(data);
        infoPanelSpinner.classList.add('hidden');
        infoPanel.classList.remove('hidden');
      }

      // Store the file tree data in localStorage
      try {
        localStorage.setItem('fileTree', JSON.stringify(data.file_tree));
        console.log('File tree saved to localStorage');
      } catch (e) {
        console.error('Error saving file tree:', e);
      }
    },
    // onError - task failed
    function (error) {
      // 404 Not Found means the task is still pending, so we'll continue polling
    },
    // onProgress - task still running
    function (status) {
      console.log('Repository analysis in progress:', status);
      // Could update progress indicators here if needed
    },
  );
});

/**
 * Update the file tree display with the given data
 *
 * @param {Array} fileTreeData - The file tree data to display
 */
function updateFileTree(fileTreeData) {
  // Find the project tree container
  const projectTreeContainer = document.getElementById('project-tree');
  if (!projectTreeContainer) {
    console.error('Could not find project tree container');
    return;
  }

  // Update total token count
  const totalTokenCountEl = document.getElementById('total-token-count');
  if (totalTokenCountEl) {
    // Calculate total tokens from file tree data
    const totalTokens = calculateTotalTokens(fileTreeData);
    totalTokenCountEl.textContent = totalTokens;
  }

  // Render file tree recursively
  const treeContainer = document.querySelector('#project-tree ul');
  if (treeContainer) {
    // Clear existing tree
    treeContainer.innerHTML = '';

    // Render new tree nodes
    renderFileTree(fileTreeData, treeContainer);
  } else {
    console.error('Could not find file tree ul element');
  }

  // Initialize file tree event listeners
  initializeFileTreeEventListeners();

  // Dispatch a custom event to notify any components that depend on the file tree
  document.dispatchEvent(
    new CustomEvent('fileTreeUpdated', {
      detail: { fileTree: fileTreeData },
    }),
  );
}

/**
 * Calculate total token count from file tree
 *
 * @param {Array} fileTree - The file tree data
 * @returns {number} - Total token count
 */
function calculateTotalTokens(fileTree) {
  let totalTokens = 0;

  fileTree.forEach((item) => {
    if (item.token_count) {
      totalTokens += item.token_count;
    }

    if (item.children && item.children.length > 0) {
      totalTokens += calculateTotalTokens(item.children);
    }
  });

  return totalTokens;
}

/**
 * Render file tree nodes recursively
 *
 * @param {Array} fileTree - The file tree data
 * @param {HTMLElement} container - The container to render into
 */
function renderFileTree(fileTree, container) {
  fileTree.forEach((item) => {
    const li = document.createElement('li');
    li.className = 'mb-2';

    if (item.is_dir) {
      const details = document.createElement('details');
      details.className = 'group';

      const summary = document.createElement('summary');
      summary.className =
        'flex items-center cursor-pointer text-gray-700 dark:text-gray-200 font-semibold hover:underline';

      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.className = 'mr-1 folder-checkbox fb-checkbox';
      checkbox.dataset.path = item.path;
      checkbox.dataset.isDir = 'true';
      checkbox.dataset.tokenCount = item.token_count || 0;
      if (item.selected) checkbox.checked = true;

      const folderIcon = document.createElement('span');
      folderIcon.className = 'mr-1';
      folderIcon.textContent = '📁';
      const folderName = document.createTextNode(item.name);

      const tokenSpan = document.createElement('span');
      tokenSpan.className = 'ml-2 dark:text-gray-400';
      tokenSpan.textContent = `(${item.token_count || 0} tokens)`;

      summary.appendChild(checkbox);
      summary.appendChild(folderIcon);
      summary.appendChild(folderName);
      summary.appendChild(tokenSpan);

      details.appendChild(summary);

      if (item.children && item.children.length > 0) {
        const childContainer = document.createElement('div');
        childContainer.className = 'pl-4 border-l border-gray-300 mt-2';

        const childUl = document.createElement('ul');
        childUl.className = 'list-none px-4 text-xs';
        childContainer.appendChild(childUl);

        renderFileTree(item.children, childUl);
        details.appendChild(childContainer);
      }

      li.appendChild(details);
    } else {
      const div = document.createElement('div');
      div.className =
        'flex items-center dark:text-gray-100 dark:hover:text-white';

      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.className = 'mr-1 file-checkbox fb-checkbox';
      checkbox.dataset.path = item.path;
      checkbox.dataset.isDir = 'false';
      checkbox.dataset.tokenCount = item.token_count || 0;
      if (item.selected) checkbox.checked = true;

      const fileIcon = document.createElement('span');
      fileIcon.className = 'mr-1';
      fileIcon.textContent = '📄';
      const nameSpan = document.createElement('span');
      nameSpan.className = '';
      nameSpan.textContent = item.name;

      const tokenSpan = document.createElement('span');
      tokenSpan.className = 'ml-2 dark:text-gray-400';
      tokenSpan.textContent = `(${item.token_count || 0} tokens)`;

      div.appendChild(checkbox);
      div.appendChild(fileIcon);
      div.appendChild(nameSpan);
      div.appendChild(tokenSpan);

      li.appendChild(div);
    }

    container.appendChild(li);
  });
}

/**
 * Initialize event listeners for the file tree
 */
function initializeFileTreeEventListeners() {
  // Add event listeners for checkboxes, folder expansion, etc.
  const checkboxes = document.querySelectorAll('.fb-checkbox');
  checkboxes.forEach((checkbox) => {
    checkbox.addEventListener('change', function () {
      // Handle checkbox selection events
      const isDir = this.dataset.isDir === 'true';
      const path = this.dataset.path;
      const isChecked = this.checked;

      if (isDir) {
        // If directory, select/deselect all children
        const childCheckboxes =
          this.closest('details').querySelectorAll('.fb-checkbox');
        childCheckboxes.forEach((child) => {
          child.checked = isChecked;
        });
      }

      // Update token counts or other state as needed
      updateSelectionState();
    });
  });
}

/**
 * Update the selection state and token counts
 */
function updateSelectionState() {
  // This would update any UI that depends on the selection
  // For example, updating the selected token count
  const selectedCheckboxes = document.querySelectorAll('.fb-checkbox:checked');
  let selectedTokens = 0;

  selectedCheckboxes.forEach((checkbox) => {
    if (!checkbox.dataset.isDir || checkbox.dataset.isDir === 'false') {
      selectedTokens += parseInt(checkbox.dataset.tokenCount || 0, 10);
    }
  });

  // Update UI with selected token count if needed
}

/**
 * Get a list of all selected files with their full paths
 *
 * @returns {Array} - Array of file paths that are selected
 */
function getSelectedFiles() {
  const selectedCheckboxes = document.querySelectorAll('.fb-checkbox:checked');
  let selectedFiles = [];
  // Loop through each checkbox and add file paths to the array
  selectedCheckboxes.forEach((checkbox) => {
    // Only include files, not directories
    if (checkbox.dataset.isDir === 'false') {
      selectedFiles.push(checkbox.dataset.path);
    }
  });

  return selectedFiles;
}

/**
 * Update the info panel with the repository analysis data
 *
 * @param {Object} data - The repository analysis data
 */
function updateInfoPanel(data) {
  // Update the component count
  const componentCountElement = document.getElementById('component-count');
  if (componentCountElement && data.component_count) {
    componentCountElement.textContent = data.component_count;
  }

  // Update the file count
  const fileCountElement = document.getElementById('file-count');
  if (fileCountElement && data.file_count) {
    fileCountElement.textContent = data.file_count;
  }

  // Update the token count
  const tokenCountElement = document.getElementById('token-count');
  if (tokenCountElement && data.token_count) {
    tokenCountElement.textContent = data.token_count;
  }

  // Update technologies list
  const technologiesElement = document.getElementById('technologies-list');
  if (
    technologiesElement &&
    data.technologies &&
    data.technologies.length > 0
  ) {
    technologiesElement.innerHTML = ''; // Clear existing content

    data.technologies.forEach((tech) => {
      const techItem = document.createElement('span');
      techItem.className =
        'inline-block bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded mr-1 mb-1';
      techItem.textContent = tech;
      technologiesElement.appendChild(techItem);
    });
  }

  // Update topics list
  const topicsElement = document.getElementById('topics-list');
  if (topicsElement && data.topics && data.topics.length > 0) {
    topicsElement.innerHTML = ''; // Clear existing content

    data.topics.forEach((topic) => {
      const topicItem = document.createElement('span');
      topicItem.className =
        'inline-block bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-100 px-2 py-1 rounded mr-1 mb-1';
      topicItem.textContent = topic;
      topicsElement.appendChild(topicItem);
    });
  }
}
