/**
 * mermaid-pan-zoom.js - Add pan and zoom functionality to Mermaid diagrams
 */

class MermaidPanZoom {
  constructor(containerSelector = '.mermaid', options = {}) {
    this.containerSelector = containerSelector;
    this.options = {
      zoomFactor: options.zoomFactor || 0.1,
      minZoom: options.minZoom || 0.5,
      maxZoom: options.maxZoom || 3,
      panStep: options.panStep || 50, // Step size for pan controls
      ...options,
    };

    this.containers = [];
    this.svgElements = [];
    this.panEnabled = false;
    this.startX = 0;
    this.startY = 0;
    this.lastX = 0;
    this.lastY = 0;
    this.currentZoom = 1;
    this.currentX = 0;
    this.currentY = 0;

    this.init();
  }

  init() {
    // Wait for document to be fully loaded
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }

  setup() {
    this.initObserver();

    // Initial setup for existing mermaid diagrams
    this.containers = document.querySelectorAll(this.containerSelector);
    this.setupExistingDiagrams();

    // Add controls to each diagram container
    this.addControls();
  }

  initObserver() {
    // Use MutationObserver to detect when new diagrams are rendered
    this.observer = new MutationObserver((mutations) => {
      let diagramsUpdated = false;

      for (const mutation of mutations) {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
          for (const node of mutation.addedNodes) {
            if (node.nodeType === Node.ELEMENT_NODE) {
              // Check if the added node is an SVG or contains SVG elements
              if (node.tagName === 'svg' || node.querySelector('svg')) {
                diagramsUpdated = true;
                break;
              }
            }
          }
        }
      }

      if (diagramsUpdated) {
        // Re-setup diagrams after a small delay to ensure rendering is complete
        setTimeout(() => {
          this.containers = document.querySelectorAll(this.containerSelector);
          this.setupExistingDiagrams();
          this.addControls();
        }, 100);
      }
    });

    // Observe the entire document for changes
    this.observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  }

  setupExistingDiagrams() {
    this.containers.forEach((container) => {
      // Find the SVG element inside the container
      const svg = container.querySelector('svg');

      if (svg && !svg.hasAttribute('data-pan-zoom-initialized')) {
        this.setupSvg(svg, container);
        svg.setAttribute('data-pan-zoom-initialized', 'true');
      }
    });
  }

  setupSvg(svg, container) {
    // Store initial viewBox values
    const viewBox = svg.getAttribute('viewBox');
    if (viewBox) {
      const [x, y, width, height] = viewBox.split(' ').map(Number);
      svg.dataset.originalViewBox = viewBox;
      svg.dataset.viewBoxX = x;
      svg.dataset.viewBoxY = y;
      svg.dataset.viewBoxWidth = width;
      svg.dataset.viewBoxHeight = height;
    }

    // Add event listeners for pan/zoom functionality
    this.addPanEventListeners(svg);
    this.addZoomEventListeners(svg, container);

    // Store reference to the SVG
    this.svgElements.push(svg);
  }

  addPanEventListeners(svg) {
    svg.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return; // Only respond to left mouse button

      this.panEnabled = true;
      this.startX = e.clientX;
      this.startY = e.clientY;
      this.lastX = this.currentX;
      this.lastY = this.currentY;

      svg.style.cursor = 'grabbing';
      e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
      if (!this.panEnabled) return;

      const dx = e.clientX - this.startX;
      const dy = e.clientY - this.startY;

      this.currentX = this.lastX + dx;
      this.currentY = this.lastY + dy;

      this.updateSvgTransform(svg);
      e.preventDefault();
    });

    document.addEventListener('mouseup', () => {
      if (this.panEnabled) {
        this.panEnabled = false;
        svg.style.cursor = 'grab';
      }
    });

    // Add touch support for mobile devices
    svg.addEventListener('touchstart', (e) => {
      if (e.touches.length !== 1) return;

      this.panEnabled = true;
      this.startX = e.touches[0].clientX;
      this.startY = e.touches[0].clientY;
      this.lastX = this.currentX;
      this.lastY = this.currentY;

      e.preventDefault();
    });

    document.addEventListener('touchmove', (e) => {
      if (!this.panEnabled || e.touches.length !== 1) return;

      const dx = e.touches[0].clientX - this.startX;
      const dy = e.touches[0].clientY - this.startY;

      this.currentX = this.lastX + dx;
      this.currentY = this.lastY + dy;

      this.updateSvgTransform(svg);
      e.preventDefault();
    });

    document.addEventListener('touchend', () => {
      this.panEnabled = false;
    });
  }

  addZoomEventListeners(svg, container) {
    // Mouse wheel zoom
    container.addEventListener(
      'wheel',
      (e) => {
        e.preventDefault();

        // Determine zoom direction
        const delta = e.deltaY < 0 ? 1 : -1;
        const zoomFactor = this.options.zoomFactor * delta;

        // Calculate new zoom level
        const newZoom = Math.max(
          this.options.minZoom,
          Math.min(this.options.maxZoom, this.currentZoom + zoomFactor),
        );

        // Calculate zoom point (relative to SVG)
        const containerRect = container.getBoundingClientRect();
        const mouseX = e.clientX - containerRect.left;
        const mouseY = e.clientY - containerRect.top;

        // Apply zoom
        this.applyZoom(svg, newZoom, mouseX, mouseY);
      },
      { passive: false },
    );
  }

  applyZoom(svg, newZoom, mouseX, mouseY) {
    // Calculate how much we're zooming by
    const zoomRatio = newZoom / this.currentZoom;

    // Update the current zoom level
    this.currentZoom = newZoom;

    // Update SVG transform
    this.updateSvgTransform(svg);

    // Display current zoom level in info box (if exists)
    const infoBox = svg
      .closest('.mermaid-container')
      ?.querySelector('.zoom-info');
    if (infoBox) {
      infoBox.textContent = `Zoom: ${Math.round(this.currentZoom * 100)}%`;

      // Show the info box briefly
      infoBox.classList.add('visible');
      clearTimeout(this.infoTimeout);
      this.infoTimeout = setTimeout(() => {
        infoBox.classList.remove('visible');
      }, 1500);
    }
  }

  updateSvgTransform(svg) {
    // Apply transform for pan and zoom
    svg.style.transform = `translate(${this.currentX}px, ${this.currentY}px) scale(${this.currentZoom})`;
    svg.style.transformOrigin = '0 0';
  }

  resetView(svg) {
    // Reset to original view
    this.currentZoom = 1;
    this.currentX = 0;
    this.currentY = 0;
    this.updateSvgTransform(svg);
  }

  // Method to pan in a specific direction
  panDirection(svg, direction) {
    const panStep = this.options.panStep / this.currentZoom;

    switch (direction) {
      case 'up':
        this.currentY += panStep;
        break;
      case 'down':
        this.currentY -= panStep;
        break;
      case 'left':
        this.currentX += panStep;
        break;
      case 'right':
        this.currentX -= panStep;
        break;
    }

    this.updateSvgTransform(svg);

    // Show pan info if it exists
    const infoBox = svg
      .closest('.mermaid-container')
      ?.querySelector('.zoom-info');
    if (infoBox) {
      infoBox.textContent = `Pan: ${direction}`;
      infoBox.classList.add('visible');
      clearTimeout(this.infoTimeout);
      this.infoTimeout = setTimeout(() => {
        infoBox.classList.remove('visible');
      }, 1000);
    }
  }

  addControls() {
    if (document.getElementById('id-mermaid-controls')) return;
    this.containers.forEach((container) => {
      const svg = container.querySelector('svg');
      if (!svg || container.querySelector('.mermaid-controls')) return;

      // Create a parent container if needed
      let parentContainer = container.closest('.mermaid-container');

      if (!parentContainer) {
        // Create a wrapper container
        parentContainer = document.createElement('div');
        parentContainer.className = 'mermaid-container';
        container.parentNode.insertBefore(parentContainer, container);
        parentContainer.appendChild(container);
      }

      // Create control elements
      const controls = document.createElement('div');
      controls.className = 'mermaid-controls';
      controls.id = 'id-mermaid-controls';
      controls.innerHTML = `
        <button class="zoom-in" title="Zoom In">
        <svg class="w-6 h-6 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">
          <path stroke="currentColor" stroke-linecap="round" stroke-width="2" d="m21 21-3.5-3.5M10 7v6m-3-3h6m4 0a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z"/>
        </svg>
        </button>
        <button class="zoom-out" title="Zoom Out">
        <svg class="w-6 h-6 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">
            <path stroke="currentColor" stroke-linecap="round" stroke-width="2" d="m21 21-3.5-3.5M7 10h6m4 0a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z"/>
        </svg>
        </button>
        <div class="pan-controls">
          <button class="pan-up" title="Pan Up">
          <svg class="w-6 h-6 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">
              <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v13m0-13 4 4m-4-4-4 4"/>
            </svg>
          </button>
          <div class="pan-horizontal">
            <button class="pan-left" title="Pan Left">
            <svg class="w-6 h-6 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">
              <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12l4-4m-4 4 4 4"/>
            </svg>
            </button>
            <button class="pan-right" title="Pan Right">
            <svg class="w-6 h-6 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">
              <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 12H5m14 0-4 4m4-4-4-4"/>
            </svg>
            </button>
          </div>

          <button class="pan-down" title="Pan Down">
            <svg class="w-6 h-6 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">
              <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19V5m0 14-4-4m4 4 4-4"/>
            </svg>
          </button>
        </div>
        <button class="reset-view" title="Reset View">
            <svg class="w-6 h-6 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">
              <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.651 7.65a7.131 7.131 0 0 0-12.68 3.15M18.001 4v4h-4m-7.652 8.35a7.13 7.13 0 0 0 12.68-3.15M6 20v-4h4"/>
            </svg>
        </button>
      `;

      // Fix: Check if container is a direct child of parentContainer before using insertBefore
      if (Array.from(parentContainer.children).includes(container)) {
        // Insert controls before the mermaid diagram if container is a direct child
        parentContainer.insertBefore(controls, container);
      } else {
        // Otherwise just prepend it to the parent container
        parentContainer.prepend(controls);
      }
      // Add event listeners to buttons
      controls.querySelector('.zoom-in').addEventListener('click', () => {
        const newZoom = Math.min(
          this.options.maxZoom,
          this.currentZoom + this.options.zoomFactor,
        );
        this.applyZoom(svg, newZoom);
      });

      controls.querySelector('.zoom-out').addEventListener('click', () => {
        const newZoom = Math.max(
          this.options.minZoom,
          this.currentZoom - this.options.zoomFactor,
        );
        this.applyZoom(svg, newZoom);
      });

      controls.querySelector('.reset-view').addEventListener('click', () => {
        this.resetView(svg);
      });

      // Add event listeners for pan controls
      controls.querySelector('.pan-up').addEventListener('click', () => {
        this.panDirection(svg, 'up');
      });

      controls.querySelector('.pan-down').addEventListener('click', () => {
        this.panDirection(svg, 'down');
      });

      controls.querySelector('.pan-left').addEventListener('click', () => {
        this.panDirection(svg, 'left');
      });

      controls.querySelector('.pan-right').addEventListener('click', () => {
        this.panDirection(svg, 'right');
      });

      // Add keyboard navigation for accessible pan controls
      document.addEventListener('keydown', (e) => {
        // Check if we're focused on the diagram or its controls
        const activeElement = document.activeElement;
        const isFocusedOnDiagram =
          parentContainer.contains(activeElement) ||
          activeElement === document.body;

        if (!isFocusedOnDiagram) return;

        // Only handle arrow keys when diagram is focused
        switch (e.key) {
          case 'ArrowUp':
            this.panDirection(svg, 'up');
            e.preventDefault();
            break;
          case 'ArrowDown':
            this.panDirection(svg, 'down');
            e.preventDefault();
            break;
          case 'ArrowLeft':
            this.panDirection(svg, 'left');
            e.preventDefault();
            break;
          case 'ArrowRight':
            this.panDirection(svg, 'right');
            e.preventDefault();
            break;
        }
      });

      // Add styles for the controls and container
      this.addStyles();
    });
  }

  addStyles() {
    // Check if styles already added
    if (document.getElementById('mermaid-pan-zoom-styles')) return;

    const style = document.createElement('style');
    style.id = 'mermaid-pan-zoom-styles';
    style.textContent = `
      .mermaid-container {
        position: relative;
        overflow: hidden;
      }

      .mermaid {
        cursor: grab;
        overflow: visible;
      }

      .mermaid-controls {
        position: absolute;
        top: 10px;
        right: 10px;
        background: rgba(0, 0, 0, 0.6);
        border-radius: 4px;
        padding: 6px;
        z-index: 100;
        display: flex;
        gap: 4px;
        align-items: center;
        flex-wrap: wrap;
      }

      .mermaid-controls button {
        width: 28px;
        height: 28px;
        border: none;
        background: #555;
        color: white;
        border-radius: 3px;
        cursor: pointer;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background 0.2s;
      }

      .mermaid-controls button:hover {
        background: #777;
      }

      .mermaid-controls button:active {
        background: #333;
      }

      .pan-controls {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        margin: 0 4px;
      }

      .pan-horizontal {
        display: flex;
        gap: 2px;
      }

      .zoom-info {
        color: white;
        font-size: 12px;
        margin-left: 4px;
        opacity: 0;
        transition: opacity 0.2s;
        display: flex;
        align-items: center;
        min-width: 70px;
      }

      .zoom-info.visible {
        opacity: 1;
      }
    `;

    document.head.appendChild(style);
  }
}

// Auto-initialize when script is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Initialize for any mermaid diagram that appears on the page
  window.mermaidPanZoom = new MermaidPanZoom();
});

// Expose to window for external use
window.MermaidPanZoom = MermaidPanZoom;
