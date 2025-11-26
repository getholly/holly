/**
 * This script ensures the token counter is initialized correctly when the diagram tab is active
 */
document.addEventListener('DOMContentLoaded', function () {
  // Find the diagram tab
  const diagramTab = document.getElementById('diagram-tab');

  if (diagramTab) {
    // Add a click event listener to reinitialize token counter
    diagramTab.addEventListener('click', function () {
      // Delay the initialization to ensure DOM is fully updated
      setTimeout(function () {
        // Reinitialize the token counter if the function is available
        if (typeof window.initTokenCounter === 'function') {
          window.initTokenCounter();
        }
      }, 500);
    });
  }

  // Check if diagram mode is active via URL parameter
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('ac') === 'diagram') {
    // Diagram mode is active on page load, initialize with delay
    setTimeout(function () {
      if (typeof window.initTokenCounter === 'function') {
        window.initTokenCounter();
      }
    }, 1500); // Longer delay for initial load
  }
});
