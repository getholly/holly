/**
 * Onboarding Tour for GitHubMe
 * This script implements an interactive tour for new users
 */

document.addEventListener('DOMContentLoaded', () => {
  // Helper function to get CSRF token from cookie
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  }

  // Get the CSRF token from the cookie or form
  function getCSRFToken() {
    // Try to get from form
    const csrfInput = document.querySelector(
      'input[name="csrfmiddlewaretoken"]',
    );
    if (csrfInput) {
      return csrfInput.value;
    }

    // Try to get from header
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    if (csrfMeta) {
      return csrfMeta.getAttribute('content');
    }

    // Fallback to cookie
    return getCookie('csrftoken');
  }

  // Tour configuration
  const tour = {
    currentStep: 0,
    isActive: false,

    steps: [
      {
        element: '#sidebar',
        title: 'Repository Files',
        text: 'Select or filter the files you want to analyze. You can search for specific files and toggle their selection.',
        position: 'right',
      },
      {
        element: '#token-counter',
        title: 'Token Counter',
        text: 'Monitor your token usage here. Keep the total under 1 million tokens for optimal performance.',
        position: 'bottom',
      },
      {
        element: '#default-tab',
        title: 'Feature Tabs',
        text: 'Switch between different views of your repository:',
        position: 'bottom',
      },
      {
        element: '#standard-tab',
        title: 'Chat Mode',
        text: 'Ask questions about your code and get intelligent responses.',
        position: 'bottom',
      },
      {
        element: '#diagram-tab',
        title: 'Architecture Diagram',
        text: 'Visualize your project architecture and understand code relationships.',
        position: 'bottom',
      },
      {
        element: '#source-code-tab',
        title: 'Source Code View',
        text: 'Browse the concatenated source code from selected files.',
        position: 'bottom',
      },
    ],

    start() {
      console.log('Starting tour...');
      // Create tour elements if they don't exist
      this.createTourElements();

      // Reset to first step
      this.currentStep = 0;
      this.isActive = true;

      // Start the tour
      this.showStep(this.currentStep);

      // Add event listener for ESC key to exit tour
      document.addEventListener('keydown', this.handleEscKey);

      // Add tour-active class to body
      document.body.classList.add('tour-active');
    },

    createTourElements() {
      // Remove existing tour elements to avoid duplicates
      document
        .querySelectorAll('.tour-tooltip, .tour-backdrop, .tour-highlight')
        .forEach((el) => el.remove());

      // Create tooltip element
      const tooltip = document.createElement('div');
      tooltip.className = 'tour-tooltip';
      tooltip.innerHTML = `
    <div class="tour-tooltip-content">
      <h3 class="tour-title"></h3>
      <p class="tour-text"></p>
      <div class="tour-controls">
        <button class="tour-prev">Previous</button>
        <span class="tour-progress"></span>
        <button class="tour-next">Next</button>
      </div>
    </div>
  `;
      document.body.appendChild(tooltip);

      // Add event listeners to controls
      tooltip
        .querySelector('.tour-next')
        .addEventListener('click', () => this.next());
      tooltip
        .querySelector('.tour-prev')
        .addEventListener('click', () => this.prev());

      // Create backdrop/highlight elements
      const backdrop = document.createElement('div');
      backdrop.className = 'tour-backdrop';
      document.body.appendChild(backdrop);

      const highlight = document.createElement('div');
      highlight.className = 'tour-highlight';
      document.body.appendChild(highlight);
    },

    showStep(index) {
      // Get current step
      const step = this.steps[index];
      if (!step) return this.end();

      // Find target element
      const element = document.querySelector(step.element);
      if (!element) {
        console.error(`Tour element not found: ${step.element}`);
        this.next(); // Skip to next step
        return;
      }

      // Run beforeShow function if exists
      if (typeof step.beforeShow === 'function') {
        step.beforeShow();
      }

      // Small delay to allow tab switching if needed
      setTimeout(() => {
        // Update tooltip content
        const tooltip = document.querySelector('.tour-tooltip');
        if (!tooltip) {
          console.error('Tour tooltip not found!');
          return;
        }

        tooltip.querySelector('.tour-title').textContent = step.title;
        tooltip.querySelector('.tour-text').textContent = step.text;
        tooltip.querySelector('.tour-progress').textContent =
          `${index + 1} / ${this.steps.length}`;

        // Enable/disable prev/next buttons
        tooltip.querySelector('.tour-prev').disabled = index === 0;
        tooltip.querySelector('.tour-next').textContent =
          index === this.steps.length - 1 ? 'Finish' : 'Next';

        // Position highlight
        const rect = element.getBoundingClientRect();
        const highlight = document.querySelector('.tour-highlight');

        highlight.style.top = `${rect.top + window.scrollY}px`;
        highlight.style.left = `${rect.left + window.scrollX}px`;
        highlight.style.width = `${rect.width}px`;
        highlight.style.height = `${rect.height}px`;
        highlight.style.display = 'block';

        // Position tooltip based on specified position
        const tooltipRect = tooltip.getBoundingClientRect();
        let top, left;

        switch (step.position) {
          case 'top':
            top = rect.top - tooltipRect.height - 10;
            left = rect.left + rect.width / 2 - tooltipRect.width / 2;
            break;
          case 'bottom':
            top = rect.bottom + 10;
            left = rect.left + rect.width / 2 - tooltipRect.width / 2;
            break;
          case 'left':
            top = rect.top + rect.height / 2 - tooltipRect.height / 2;
            left = rect.left - tooltipRect.width - 10;
            break;
          case 'right':
          default:
            top = rect.top + rect.height / 2 - tooltipRect.height / 2;
            left = rect.right + 10;
            break;
        }

        // Ensure tooltip stays within viewport
        if (top < 0) top = 10;
        if (left < 0) left = 10;
        if (top + tooltipRect.height > window.innerHeight) {
          top = window.innerHeight - tooltipRect.height - 10;
        }
        if (left + tooltipRect.width > window.innerWidth) {
          left = window.innerWidth - tooltipRect.width - 10;
        }

        tooltip.style.top = `${top + window.scrollY}px`;
        tooltip.style.left = `${left + window.scrollX}px`;
        tooltip.style.display = 'block';
      }, 300);
    },

    next() {
      this.currentStep++;
      if (this.currentStep < this.steps.length) {
        this.showStep(this.currentStep);
      } else {
        this.end();
      }
    },

    prev() {
      if (this.currentStep > 0) {
        this.currentStep--;
        this.showStep(this.currentStep);
      }
    },

    handleEscKey(e) {
      if (e.key === 'Escape' && window.tour && window.tour.isActive) {
        window.tour.end();
      }
    },

    end() {
      // Hide tour elements
      const tooltip = document.querySelector('.tour-tooltip');
      const highlight = document.querySelector('.tour-highlight');
      const backdrop = document.querySelector('.tour-backdrop');

      if (tooltip) tooltip.style.display = 'none';
      if (highlight) highlight.style.display = 'none';
      if (backdrop) backdrop.style.display = 'none';

      // Remove ESC key event listener
      document.removeEventListener('keydown', this.handleEscKey);

      // Update local storage to remember tour completion
      if (window.localStorage) {
        window.localStorage.setItem('githubme_tour_completed', 'true');

        // Send tour completion to server
        const csrfToken = getCSRFToken();

        fetch('/_users/tour/complete/', {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
          },
        }).catch((error) =>
          console.error('Failed to mark tour as completed:', error),
        );
      }

      // Remove tour-active class from body
      document.body.classList.remove('tour-active');

      this.isActive = false;

      // Reset to first tab
      // if (window.Alpine) {
      //   const tabManager = Alpine.evaluate(
      //     document.querySelector('[x-data="tabManager"]'),
      //     'setActiveTab',
      //   );
      //   if (tabManager) tabManager('standard');
      // }
    },
  };

  // Expose tour object to global scope
  window.tour = tour;

  // Check if this is the analyze repo page (where the tour should run)
  const isAnalyzeRepoPage =
    document.querySelector('#sidebar-container') !== null;

  if (isAnalyzeRepoPage) {
    // Check if the user is new (hasn't completed the tour)
    const tourCompleted =
      window.localStorage &&
      window.localStorage.getItem('githubme_tour_completed') === 'true';

    // Add event listener to the existing tour button
    const existingTourButton = document.getElementById('tour-button');
    if (existingTourButton) {
      // Remove any existing event listeners
      const newTourButton = existingTourButton.cloneNode(true);
      existingTourButton.parentNode.replaceChild(
        newTourButton,
        existingTourButton,
      );

      // Add new event listener
      newTourButton.addEventListener('click', () => {
        console.log('Tour button clicked');
        if (window.tour) {
          window.tour.start();
        } else {
          console.error('Tour object not available');
        }
      });

      // Add animation class for new users
      if (!tourCompleted) {
        newTourButton.classList.add('tour-button-animate');
      }
    }

    // Auto-start tour for new users
    if (!tourCompleted) {
      // Slight delay to ensure all elements are loaded
      setTimeout(() => {
        if (window.tour) {
          window.tour.start();
        }
      }, 1000);
    }
  }
});
