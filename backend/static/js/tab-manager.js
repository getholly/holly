document.addEventListener('DOMContentLoaded', function () {
  // Function to get query parameters from URL
  function getQueryParams() {
    const params = new URLSearchParams(window.location.search);
    return Object.fromEntries(params.entries());
  }

  // Function to set active tab based on query parameter
  function setActiveTabFromQuery() {
    const params = getQueryParams();
    const activeTab = params.ac; // 'ac' for 'active'

    if (activeTab) {
      // Map of query parameter values to tab IDs
      const tabMapping = {
        standard: 'standard-tab',
        mermaid: 'mermaid-tab',
        diagram: 'diagram-tab',
      };

      const tabId = tabMapping[activeTab];
      if (tabId) {
        // Get the tab element
        const tab = document.getElementById(tabId);
        if (tab) {
          // Manually handle the tab activation (because Flowbite might override click event)

          // First, get the target content
          const targetId = tab.getAttribute('data-tabs-target');
          const targetContent = document.querySelector(targetId);

          // Get all tabs and content elements
          const allTabs = document.querySelectorAll('[role="tab"]');
          const allContents = document.querySelectorAll('[role="tabpanel"]');

          // Deactivate all tabs and hide all content
          allTabs.forEach((t) => {
            t.setAttribute('aria-selected', 'false');
            t.classList.remove(
              'border-blue-500',
              'active',
              'dark:text-blue-500',
              'dark:border-blue-500',
            );
            t.classList.add(
              'hover:text-gray-600',
              'hover:border-gray-300',
              'dark:hover:text-gray-300',
            );
          });

          // Activate the selected tab and show its content
          tab.setAttribute('aria-selected', 'true');
          tab.classList.add(
            'border-blue-500',
            'active',
            'dark:text-blue-500',
            'dark:border-blue-500',
          );
          tab.classList.remove(
            'hover:text-gray-600',
            'hover:border-gray-300',
            'dark:hover:text-gray-300',
          );

          if (targetContent) {
            targetContent.classList.remove('hidden');
          }

          // Also trigger the click for any custom behavior
          tab.click();
        }
      }
    }
  }

  // Function to update URL with active tab
  function updateUrlWithActiveTab(tabName) {
    // Get current URL and parameters
    const url = new URL(window.location.href);

    // Set the active tab parameter
    url.searchParams.set('ac', tabName);

    // Update browser history without reloading the page
    window.history.pushState({}, '', url.toString());
  }

  // Add click event listeners to tabs
  const tabs = document.querySelectorAll(
    '[data-tabs-toggle="#default-tab-content"]',
  );
  tabs.forEach((tabList) => {
    const tabElements = tabList.querySelectorAll('[role="tab"]');
    tabElements.forEach((tab) => {
      tab.addEventListener('click', function () {
        // Extract tab name from tab ID
        const tabName = this.id.replace('-tab', '');
        updateUrlWithActiveTab(tabName);
      });
    });
  });

  // Set active tab on page load - use a slight delay to ensure Flowbite has initialized
  setTimeout(setActiveTabFromQuery, 100);
});
