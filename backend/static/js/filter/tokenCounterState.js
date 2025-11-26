document.addEventListener('alpine:init', () => {
  Alpine.store('tokenCounter', {
    // State
    tokenCounts: {},
    selectedFiles: new Set(),
    totalTokens: 0,
    MAX_TOKENS: 1000000, // Define your max token limit here

    // Initialize
    init() {
      // Initialize with zeros (will be updated when file tree loads)
      this.totalTokens = 0;
      this.tokenCounts = {};
      this.selectedFiles = new Set();

      // Listen for file tree updates
      document.addEventListener('fileTreeUpdated', () => {
        this.recalculateTotal();
      });
    },

    // Methods
    isOverLimit() {
      return this.totalTokens > this.MAX_TOKENS;
    },

    recalculateTotal() {
      const checkedFiles = document.querySelectorAll('.file-checkbox:checked');
      let total = 0;

      checkedFiles.forEach((checkbox) => {
        const tokenCount =
          parseInt(checkbox.getAttribute('data-token-count')) || 0;
        total += tokenCount;
      });

      this.totalTokens = total;

      // Dispatch event for backward compatibility
      document.dispatchEvent(
        new CustomEvent('tokenCountUpdated', {
          detail: { totalTokens: total },
        }),
      );
    },

    addFile(path, tokenCount) {
      this.selectedFiles.add(path);
      this.tokenCounts[path] = tokenCount;
      this.totalTokens += tokenCount;
    },

    removeFile(path) {
      if (this.selectedFiles.has(path)) {
        const tokenCount = this.tokenCounts[path] || 0;
        this.selectedFiles.delete(path);
        this.totalTokens -= tokenCount;
      }
    },

    formatTokens() {
      return this.totalTokens.toLocaleString();
    },
  });
});
