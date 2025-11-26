/**
 * Token Counter Module Tests
 */

describe('Token Counter', () => {
  // Setup test DOM elements
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="project-tree">
        <div id="token-counter">
          Total: <span id="total-token-count">0</span> tokens
        </div>
        <ul class="list-none">
          <li>
            <details class="group">
              <summary>
                <input type="checkbox" class="folder-checkbox" data-path="/dir1" data-is-dir="true" data-token-count="0">
                Dir 1
              </summary>
              <div>
                <ul>
                  <li>
                    <div>
                      <input type="checkbox" class="file-checkbox" data-path="/dir1/file1.txt" data-is-dir="false" data-token-count="100">
                      File 1
                    </div>
                  </li>
                  <li>
                    <div>
                      <input type="checkbox" class="file-checkbox" data-path="/dir1/file2.txt" data-is-dir="false" data-token-count="200">
                      File 2
                    </div>
                  </li>
                </ul>
              </div>
            </details>
          </li>
          <li>
            <details class="group">
              <summary>
                <input type="checkbox" class="folder-checkbox" data-path="/dir2" data-is-dir="true" data-token-count="0">
                Dir 2
              </summary>
              <div>
                <ul>
                  <li>
                    <div>
                      <input type="checkbox" class="file-checkbox" data-path="/dir2/file3.txt" data-is-dir="false" data-token-count="300">
                      File 3
                    </div>
                  </li>
                </ul>
              </div>
            </details>
          </li>
          <li>
            <div>
              <input type="checkbox" class="file-checkbox" data-path="/file4.txt" data-is-dir="false" data-token-count="400">
              File 4
            </div>
          </li>
        </ul>
      </div>
    `;

    // Initialize token counter
    initTokenCounter();
  });

  test('Initial token count should be 0', () => {
    expect(document.getElementById('total-token-count').textContent).toBe('0');
  });

  test('Selecting a file should update the token count', () => {
    const fileCheckbox = document.querySelector(
      'input[data-path="/file4.txt"]',
    );
    fileCheckbox.checked = true;
    fileCheckbox.dispatchEvent(new Event('change'));

    expect(document.getElementById('total-token-count').textContent).toBe(
      '400',
    );
  });

  test('Selecting multiple files should add their token counts', () => {
    const file1 = document.querySelector('input[data-path="/dir1/file1.txt"]');
    const file3 = document.querySelector('input[data-path="/dir2/file3.txt"]');

    file1.checked = true;
    file1.dispatchEvent(new Event('change'));

    file3.checked = true;
    file3.dispatchEvent(new Event('change'));

    expect(document.getElementById('total-token-count').textContent).toBe(
      '400',
    );
  });

  test('Selecting a directory should select all its files', () => {
    const dir1Checkbox = document.querySelector('input[data-path="/dir1"]');
    dir1Checkbox.checked = true;
    dir1Checkbox.dispatchEvent(new Event('change'));

    const file1 = document.querySelector('input[data-path="/dir1/file1.txt"]');
    const file2 = document.querySelector('input[data-path="/dir1/file2.txt"]');

    expect(file1.checked).toBe(true);
    expect(file2.checked).toBe(true);
    expect(document.getElementById('total-token-count').textContent).toBe(
      '300',
    );
  });

  test('Deselecting a file should decrease the token count', () => {
    // First select two files
    const file1 = document.querySelector('input[data-path="/dir1/file1.txt"]');
    const file3 = document.querySelector('input[data-path="/dir2/file3.txt"]');

    file1.checked = true;
    file1.dispatchEvent(new Event('change'));

    file3.checked = true;
    file3.dispatchEvent(new Event('change'));

    // Then deselect one
    file1.checked = false;
    file1.dispatchEvent(new Event('change'));

    expect(document.getElementById('total-token-count').textContent).toBe(
      '300',
    );
  });
});
