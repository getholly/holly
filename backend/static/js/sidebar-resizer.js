/**
 * Sidebar resize functionality
 * Allows users to resize the sidebar by dragging the resize handle
 */
document.addEventListener('DOMContentLoaded', function () {
  // Configuration
  console.log('Sidebar resize script loading...');
  const minWidth = 50;
  const maxWidth = 500;
  const defaultWidth = 288; // 72px or 18rem

  // DOM Elements - Make sure to use the correct IDs
  const sidebar = document.getElementById('sidebar');
  const resizeHandle = document.getElementById('resize-handle');

  if (!sidebar || !resizeHandle) {
    console.error('Sidebar resize: Required elements not found');
  }

  // State variables
  let isResizing = false;
  let startX;
  let startWidth;

  // Initialize sidebar width from localStorage or use default
  const storedWidth = parseInt(localStorage.getItem('sidebarWidth'));
  const sidebarWidth = !isNaN(storedWidth) ? storedWidth : defaultWidth;

  // Set initial width
  updateSidebarWidth(sidebarWidth);

  // Add visual indicator class when resizing
  function addResizeClass() {
    resizeHandle.classList.add('bg-blue-300', 'dark:bg-blue-600');
    document.body.classList.add('select-none');
  }

  function removeResizeClass() {
    resizeHandle.classList.remove('bg-blue-300', 'dark:bg-blue-600');
    resizeHandle.classList.add('bg-gray-300', 'dark:bg-gray-500');
    document.body.classList.remove('select-none');
  }

  // Event listeners
  resizeHandle.addEventListener('mousedown', function (e) {
    isResizing = true;
    startX = e.clientX;
    startWidth = sidebar.offsetWidth;
    addResizeClass();
    console.log('start resizing...');
    e.preventDefault(); // Prevent text selection
  });

  document.addEventListener('mousemove', function (e) {
    if (!isResizing) return;

    const deltaX = e.clientX - startX;
    let newWidth = startWidth + deltaX;

    // Enforce constraints
    newWidth = Math.max(minWidth, Math.min(maxWidth, newWidth));

    updateSidebarWidth(newWidth);
    localStorage.setItem('sidebarWidth', newWidth);
  });

  document.addEventListener('mouseup', function () {
    if (isResizing) {
      isResizing = false;
      console.log('done mouse moved whilst resize');
      removeResizeClass();
    }
  });

  // Handle cases where mouse goes out of window
  document.addEventListener('mouseleave', function () {
    if (isResizing) {
      isResizing = false;
      removeResizeClass();
    }
  });

  function updateSidebarWidth(width) {
    sidebar.style.width = `${width}px`;
  }
});
