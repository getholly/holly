// Alpine.js Tab Manager Component
document.addEventListener('alpine:init', () => {
  Alpine.data('tabManager', () => ({
    activeTab: 'standard', // Default active tab
    tabMapping: {
      standard: '#profile',
      diagram: '#diagram',
      'source-code': '#source-code',
      'code-editor': '#code-editor',
    },

    // Initialize tabs based on URL query parameters
    init() {
      // Get active tab from URL if present
      const params = new URLSearchParams(window.location.search);
      const activeTabParam = params.get('ac');

      if (
        activeTabParam &&
        ['standard', 'diagram', 'source-code', 'code-editor'].includes(
          activeTabParam,
        )
      ) {
        this.activeTab = activeTabParam;
      }
    },

    // Check if a tab is active
    isActive(tabName) {
      return this.activeTab === tabName;
    },

    // Set the active tab and update URL
    setActiveTab(tabName) {
      this.activeTab = tabName;
      this.updateUrl();
    },

    // Update URL with active tab parameter
    updateUrl() {
      const url = new URL(window.location.href);
      url.searchParams.set('ac', this.activeTab);
      window.history.pushState({}, '', url.toString());
    },
  }));
});
