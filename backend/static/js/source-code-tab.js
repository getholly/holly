/**
 * Source Code Tab functionality
 */
document.addEventListener('DOMContentLoaded', function () {
  // Elements
  const sourceCodeTab = document.getElementById('source-code-tab');
  const sourceCodeContent = document.getElementById('source-code-content');
  const sourceCodeInfo = document.getElementById('source-code-info');
  const sourceCodeLoading = document.getElementById('source-code-loading');
  const copyButton = document.getElementById('copy-source-code');
  const downloadButton = document.getElementById('download-source-code');

  // State
  let selectedFiles = [];
  const sourceCodeData = {
    fileContents: {},
    currentContent: '',
  };

  // Debug logging
  function debugLog(message, data) {
    if (window.localStorage.getItem('debug_source_code') === 'true') {
      console.log(`[Source Code] ${message}`, data || '');
    }
  }

  // Function to get CSRF token from cookies or from the DOM
  function getCsrfToken() {
    // First try to get from the DOM (most reliable method)
    const csrfTokenElement = document.querySelector(
      'input[name="csrfmiddlewaretoken"]',
    );
    if (csrfTokenElement) {
      debugLog('CSRF Token found in DOM:', csrfTokenElement.value);
      return csrfTokenElement.value;
    }

    // Fallback to cookies
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, 'csrftoken='.length) === 'csrftoken=') {
          cookieValue = decodeURIComponent(
            cookie.substring('csrftoken='.length),
          );
          break;
        }
      }
    }
    debugLog('CSRF Token from cookies:', cookieValue);
    return cookieValue;
  }

  // Function to update the selected files
  function updateSelectedFiles() {
    const checkboxes = document.querySelectorAll('.file-checkbox:checked');
    selectedFiles = Array.from(checkboxes).map(
      (checkbox) => checkbox.dataset.path,
    );
    debugLog('Selected files updated', selectedFiles);

    if (sourceCodeTab.getAttribute('aria-selected') === 'true') {
      loadSourceCode();
    }
  }

  // Function to format code with file paths
  function formatSourceCode(fileContents) {
    let formattedCode = '';

    Object.entries(fileContents).forEach(([path, content]) => {
      formattedCode += `// --- ${path} ---\n${content}\n\n`;
    });

    return formattedCode;
  }

  // Function to load the source code
  async function loadSourceCode() {
    if (selectedFiles.length === 0) {
      sourceCodeInfo.classList.remove('hidden');
      sourceCodeContent.textContent = '';
      copyButton.disabled = true;
      downloadButton.disabled = true;
      sourceCodeData.currentContent = '';
      return;
    }

    sourceCodeInfo.classList.add('hidden');
    sourceCodeLoading.classList.remove('hidden');

    try {
      // Get current URL path components
      const pathParts = window.location.pathname.split('/');
      const username = pathParts[1];
      const repo = pathParts[2];

      const formData = new FormData();
      selectedFiles.forEach((file) =>
        formData.append('selected_files[]', file),
      );

      // Add CSRF token to the request
      const csrfToken = getCsrfToken();

      const response = await fetch(`/${username}/${repo}/source-code/`, {
        method: 'POST',
        body: formData,
        headers: {
          'X-CSRFToken': csrfToken,
        },
      });

      if (!response.ok) {
        throw new Error(
          `Failed to load source code: ${response.status} ${response.statusText}`,
        );
      }

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      sourceCodeData.fileContents = data.file_contents;
      sourceCodeData.currentContent = formatSourceCode(data.file_contents);

      // Display the formatted source code
      sourceCodeContent.textContent = sourceCodeData.currentContent;

      // Enable copy and download buttons if we have content
      const hasContent = sourceCodeData.currentContent.trim() !== '';
      copyButton.disabled = !hasContent;
      downloadButton.disabled = !hasContent;
    } catch (error) {
      console.error('Error loading source code:', error);
      sourceCodeContent.textContent = `Error loading source code: ${error.message}`;
    } finally {
      sourceCodeLoading.classList.add('hidden');
    }
  }

  // Copy source code to clipboard
  function copySourceCode() {
    if (!sourceCodeData.currentContent) return;

    navigator.clipboard
      .writeText(sourceCodeData.currentContent)
      .then(() => {
        // Show temporary success indicator
        const originalText = copyButton.textContent;
        copyButton.textContent = 'Copied!';
        copyButton.classList.remove('bg-blue-600', 'hover:bg-blue-700');
        copyButton.classList.add('bg-green-600', 'hover:bg-green-700');

        setTimeout(() => {
          copyButton.textContent = originalText;
          copyButton.classList.remove('bg-green-600', 'hover:bg-green-700');
          copyButton.classList.add('bg-blue-600', 'hover:bg-blue-700');
        }, 2000);
      })
      .catch((err) => {
        console.error('Error copying to clipboard:', err);
      });
  }

  // Download source code as a text file
  function downloadSourceCode() {
    if (!sourceCodeData.currentContent) return;

    const blob = new Blob([sourceCodeData.currentContent], {
      type: 'text/plain',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');

    a.href = url;
    a.download = 'source-code.txt';
    document.body.appendChild(a);
    a.click();

    // Cleanup
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 100);
  }

  // Event listeners
  if (sourceCodeTab) {
    sourceCodeTab.addEventListener('click', () => {
      updateSelectedFiles();
    });
  }

  // Listen for checkbox changes to update selected files
  document.body.addEventListener('change', (event) => {
    if (
      event.target.classList.contains('file-checkbox') ||
      event.target.classList.contains('folder-checkbox')
    ) {
      // Wait a bit for the checkbox state to be processed by file_tree.js
      setTimeout(() => {
        updateSelectedFiles();
      }, 100);
    }
  });

  // Add click event for copy button
  if (copyButton) {
    copyButton.addEventListener('click', copySourceCode);
  }

  // Add click event for download button
  if (downloadButton) {
    downloadButton.addEventListener('click', downloadSourceCode);
  }

  // Re-initialize when the tree is updated via HTMX
  document.body.addEventListener('htmx:afterSwap', function (event) {
    if (event.detail.target.id === 'project-tree') {
      debugLog('Tree updated via HTMX, updating selected files');
      setTimeout(() => {
        updateSelectedFiles();
      }, 100);
    }
  });

  debugLog('Source code tab initialized');
});
