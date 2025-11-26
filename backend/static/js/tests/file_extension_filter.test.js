/**
 * Unit tests for the file extension filter functionality
 */

// Import the module
const { initFileExtensionFilter } = require('../file_extension_filter');

// Mock DOM elements
let mockElements = {};

// Mock createElement function
document.createElement = jest.fn((tag) => {
  const element = {
    className: '',
    innerHTML: '',
    appendChild: jest.fn(),
    closest: jest.fn(),
    addEventListener: jest.fn(),
    querySelectorAll: jest.fn(),
    setAttribute: jest.fn(),
    getAttribute: jest.fn(),
    classList: {
      add: jest.fn(),
      remove: jest.fn(),
      contains: jest.fn(),
    },
    tagName: tag.toUpperCase(),
  };
  return element;
});

// Mock querySelector/querySelectorAll
document.querySelector = jest.fn((selector) => mockElements[selector] || null);
document.querySelectorAll = jest.fn((selector) => {
  if (selector === '.file-checkbox') {
    return [
      createMockCheckbox('.py', 100),
      createMockCheckbox('.js', 150),
      createMockCheckbox('.html', 80),
      createMockCheckbox('.css', 60),
      createMockCheckbox('.md', 120),
    ];
  }
  if (selector === '.extension-checkbox') {
    return [
      {
        checked: true,
        getAttribute: jest.fn((attr) => (attr === 'data-index' ? '0' : null)),
        addEventListener: jest.fn(),
      },
      {
        checked: false,
        getAttribute: jest.fn((attr) => (attr === 'data-index' ? '1' : null)),
        addEventListener: jest.fn(),
      },
    ];
  }
  if (selector === '.folder-checkbox') {
    return [
      {
        checked: false,
        indeterminate: false,
        closest: jest.fn(() => ({
          querySelectorAll: jest.fn(() => [
            { checked: true },
            { checked: false },
          ]),
        })),
      },
    ];
  }
  return [];
});

document.getElementById = jest.fn((id) => mockElements[`#${id}`] || null);

// Helper function to create a mock checkbox with file data
function createMockCheckbox(extension, tokenCount) {
  return {
    getAttribute: jest.fn((attr) => {
      if (attr === 'data-path') return `/path/to/file${extension}`;
      if (attr === 'data-token-count') return tokenCount.toString();
      return null;
    }),
    checked: false,
  };
}

// Setup mocks before each test
beforeEach(() => {
  jest.clearAllMocks();

  // Setup mock DOM elements
  mockElements = {
    '#project-tree button': { addEventListener: jest.fn() },
    '#file-extension-filter-modal': {
      addEventListener: jest.fn(),
      classList: { add: jest.fn(), remove: jest.fn() },
    },
    '#close-filter-modal': { addEventListener: jest.fn() },
    '#extension-list': { innerHTML: '', appendChild: jest.fn() },
    '#selected-extensions-token-count': { textContent: '0' },
    '#select-all-extensions': { addEventListener: jest.fn() },
    '#clear-all-extensions': { addEventListener: jest.fn() },
    '#apply-filter': { addEventListener: jest.fn() },
  };

  // Mock window.addEventListener
  window.addEventListener = jest.fn();
});

describe('File Extension Filter', () => {
  test('should initialize event listeners when DOM is loaded', () => {
    initFileExtensionFilter();

    // Check that event listeners are set up
    expect(
      mockElements['#project-tree button'].addEventListener,
    ).toHaveBeenCalledWith('click', expect.any(Function));
    expect(
      mockElements['#close-filter-modal'].addEventListener,
    ).toHaveBeenCalledWith('click', expect.any(Function));
    expect(
      mockElements['#select-all-extensions'].addEventListener,
    ).toHaveBeenCalledWith('click', expect.any(Function));
    expect(
      mockElements['#clear-all-extensions'].addEventListener,
    ).toHaveBeenCalledWith('click', expect.any(Function));
    expect(mockElements['#apply-filter'].addEventListener).toHaveBeenCalledWith(
      'click',
      expect.any(Function),
    );
    expect(window.addEventListener).toHaveBeenCalledWith(
      'click',
      expect.any(Function),
    );
  });

  test('should extract file extensions correctly', () => {
    initFileExtensionFilter();

    // Get the openFilterModal function
    const openFilterModalFn =
      mockElements['#project-tree button'].addEventListener.mock.calls[0][1];

    // Call openFilterModal to trigger the collection of extension data
    openFilterModalFn();

    // Check that the modal is shown
    expect(
      mockElements['#file-extension-filter-modal'].classList.remove,
    ).toHaveBeenCalledWith('hidden');

    // The extension list should be updated
    expect(mockElements['#extension-list'].innerHTML).toBe('');
  });

  // More tests could be added for:
  // - Testing the extractExtension function
  // - Testing the getReadableExtension function
  // - Testing the updateExtensionList function
  // - Testing selectAllExtensions and clearAllExtensions
  // - Testing applyFilter function
  // - etc.
});
