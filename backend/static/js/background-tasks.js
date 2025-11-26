/**
 * Background task handling for async operations.
 *
 * This module handles polling and updating the UI for
 * long-running background tasks.
 */

class BackgroundTaskManager {
  constructor() {
    this.pollingTasks = new Map();
    this.pollingInterval = 1000; // 1 second default polling interval
  }

  /**
   * Start polling for a task's status
   *
   * @param {string} taskId - The ID of the task to poll
   * @param {string} endpoint - The API endpoint to poll
   * @param {function} onSuccess - Callback when task completes successfully
   * @param {function} onError - Callback when task fails
   * @param {function} onProgress - Callback for progress updates
   */
  startPolling(taskId, endpoint, onSuccess, onError, onProgress) {
    if (this.pollingTasks.has(taskId)) {
      console.warn(`Already polling for task ${taskId}`);
      return;
    }

    const polling = {
      taskId,
      endpoint,
      onSuccess,
      onError,
      onProgress,
      intervalId: setInterval(
        () => this.pollTask(taskId),
        this.pollingInterval,
      ),
    };

    this.pollingTasks.set(taskId, polling);
    console.log(`Started polling for task ${taskId}`);

    // Do an immediate first poll
    this.pollTask(taskId);
  }

  /**
   * Stop polling for a specific task
   *
   * @param {string} taskId - The ID of the task to stop polling
   */
  stopPolling(taskId) {
    const polling = this.pollingTasks.get(taskId);

    if (polling) {
      clearInterval(polling.intervalId);
      this.pollingTasks.delete(taskId);
      console.log(`Stopped polling for task ${taskId}`);
    }
  }

  /**
   * Stop all polling tasks
   */
  stopAllPolling() {
    for (const [taskId, polling] of this.pollingTasks.entries()) {
      clearInterval(polling.intervalId);
      console.log(`Stopped polling for task ${taskId}`);
    }
    this.pollingTasks.clear();
  }

  /**
   * Poll the status of a task
   *
   * @param {string} taskId - The ID of the task to poll
   */
  async pollTask(taskId) {
    const polling = this.pollingTasks.get(taskId);

    if (!polling) {
      console.warn(`No polling data for task ${taskId}`);
      return;
    }

    try {
      const response = await fetch(polling.endpoint);

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const data = await response.json();

      if (data.status === 'completed') {
        // Task completed successfully
        console.log(`Task ${taskId} completed successfully`);
        if (polling.onSuccess) {
          polling.onSuccess(data.data);
        }
        this.stopPolling(taskId);
      } else if (data.status === 'failed') {
        // Task failed
        console.error(`Task ${taskId} failed: ${data.error}`);
        if (polling.onError) {
          polling.onError(data.error);
        }
        this.stopPolling(taskId);
      } else {
        // Task still in progress
        if (polling.onProgress) {
          polling.onProgress(data.status);
        }
      }
    } catch (error) {
      console.error(`Error polling task ${taskId}:`, error);
      // Don't stop polling on network errors, but do call the error callback
      if (polling.onError) {
        polling.onError(error.message);
      }
    }
  }
}

// Create a global instance
window.taskManager = new BackgroundTaskManager();
