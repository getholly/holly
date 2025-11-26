/**
 * Conversation Manager - Handles conversation history functionality
 */
document.addEventListener('DOMContentLoaded', function() {
  // Function to get selected files from the file tree
  window.getSelectedFiles = function() {
    const fileTree = JSON.parse(localStorage.getItem('fileTree') || '[]');
    if (!fileTree || !fileTree.length) {
      console.warn('No file tree data available');
      return [];
    }
    return fileTree;
  };

  // Handle conversation created event
  document.addEventListener('conversationCreated', function(event) {
    if (event.detail && event.detail.id) {
      // Store the conversation ID in localStorage
      localStorage.setItem('currentConversationId', event.detail.id);
      
      // Refresh the conversation list
      const sidebarContainer = document.querySelector('[hx-get*="conversations:sidebar"]');
      if (sidebarContainer) {
        htmx.trigger(sidebarContainer, 'htmx:load');
      }
    }
  });

  // Handle conversation deleted event
  document.addEventListener('conversationDeleted', function() {
    // If the current conversation was deleted, clear it
    const currentId = localStorage.getItem('currentConversationId');
    if (currentId) {
      // Check if the conversation still exists by refreshing the sidebar
      const sidebarContainer = document.querySelector('[hx-get*="conversations:sidebar"]');
      if (sidebarContainer) {
        htmx.trigger(sidebarContainer, 'htmx:load');
      }
    }
  });

  // Handle conversation title updated
  document.addEventListener('conversationTitleUpdated', function() {
    // Refresh the conversation list
    const sidebarContainer = document.querySelector('[hx-get*="conversations:sidebar"]');
    if (sidebarContainer) {
      htmx.trigger(sidebarContainer, 'htmx:load');
    }
  });

  // Switch to a conversation from history
  window.loadConversation = function(id) {
    // Store the ID and initiate the loading
    localStorage.setItem('currentConversationId', id);
    
    // Make an HTMX request to load the conversation
    htmx.ajax('GET', `/conversations/load/${id}/`, {target: '#chat-container', swap: 'innerHTML'});
  };

  // Create a new conversation
  window.createNewConversation = function() {
    // Clear the current conversation ID
    localStorage.removeItem('currentConversationId');
    
    // Clear the chat container and add the initial message
    const chatContainer = document.getElementById('chat-container');
    if (chatContainer) {
      chatContainer.innerHTML = '<div class="ai-message"><div class="prose dark:prose-invert"><p>How can I help you with your project today?</p></div></div>';
    }
  };
});
