/**
 * Voice Transcription Module
 *
 * This module handles audio recording and transcription of voice input.
 */

class VoiceTranscription {
  constructor() {
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.isRecording = false;
    this.stream = null;
    this.modalElement = null;
    this.textareaElement = null;
    this.recordButtonElement = null;
    this.closeButtonElement = null;
    this.saveButtonElement = null;
    this.transcriptionStatusElement = null;
  }

  /**
   * Initialize the voice transcription functionality
   */
  init() {
    // Find the voice record button
    const voiceRecordButton = document.getElementById('voice-record');
    if (!voiceRecordButton) {
      console.error('Voice record button not found');
      return;
    }

    // Create modal if it doesn't exist
    this._createModal();

    // Add event listener to the voice record button
    voiceRecordButton.addEventListener('click', () => {
      this.showModal();
    });

    // Add event listeners to modal buttons
    this.recordButtonElement.addEventListener('click', () => {
      if (this.isRecording) {
        this.stopRecording();
      } else {
        this.startRecording();
      }
    });

    this.closeButtonElement.addEventListener('click', () => {
      this.hideModal();
    });

    this.saveButtonElement.addEventListener('click', () => {
      this.saveTranscription();
    });

    console.log('Voice transcription initialized');
  }

  /**
   * Create the modal element for voice recording
   */
  _createModal() {
    // Create modal element if it doesn't exist
    if (!document.getElementById('voice-transcription-modal')) {
      const modalHtml = `
        <div id="voice-transcription-modal" class="fixed inset-0 bg-gray-900 bg-opacity-75 flex items-center justify-center z-50 hidden">
          <div class="bg-gray-800 rounded-lg shadow-lg p-6 w-full max-w-md">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-xl font-semibold text-white">Voice to Text</h3>
              <button id="voice-modal-close" class="text-gray-400 hover:text-white">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>
            <div class="mb-4">
              <textarea id="transcription-text" class="w-full h-32 p-2 bg-gray-700 text-white rounded-lg" placeholder="Your transcription will appear here..."></textarea>
            </div>
            <div id="transcription-status" class="text-sm text-gray-400 mb-4 hidden">Processing...</div>
            <div class="flex justify-between">
              <button id="voice-record-button" class="px-4 py-2 bg-red-600 text-white rounded-lg flex items-center">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path>
                </svg>
                Start Recording
              </button>
              <button id="voice-save-button" class="px-4 py-2 bg-purple-600 text-white rounded-lg" disabled>
                Save Text
              </button>
            </div>
          </div>
        </div>
      `;

      const modalContainer = document.createElement('div');
      modalContainer.innerHTML = modalHtml;
      document.body.appendChild(modalContainer.firstElementChild);
    }

    // Cache DOM elements
    this.modalElement = document.getElementById('voice-transcription-modal');
    this.textareaElement = document.getElementById('transcription-text');
    this.recordButtonElement = document.getElementById('voice-record-button');
    this.closeButtonElement = document.getElementById('voice-modal-close');
    this.saveButtonElement = document.getElementById('voice-save-button');
    this.transcriptionStatusElement = document.getElementById(
      'transcription-status',
    );
  }

  /**
   * Show the recording modal
   */
  showModal() {
    if (this.modalElement) {
      this.modalElement.classList.remove('hidden');
      this.textareaElement.value = '';
      this.saveButtonElement.disabled = true;

      // Reset recording state
      this.isRecording = false;
      this.updateRecordButtonUI();
    }
  }

  /**
   * Hide the recording modal
   */
  hideModal() {
    if (this.modalElement) {
      // If still recording, stop it
      if (this.isRecording) {
        this.stopRecording();
      }

      this.modalElement.classList.add('hidden');
    }
  }

  /**
   * Start recording audio
   */
  async startRecording() {
    try {
      // Request permission to access the microphone
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Create MediaRecorder instance
      this.mediaRecorder = new MediaRecorder(this.stream);
      this.audioChunks = [];

      // Add event listeners
      this.mediaRecorder.addEventListener('dataavailable', (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      });

      this.mediaRecorder.addEventListener('stop', () => {
        this.processAudio();
      });

      // Start recording
      this.mediaRecorder.start();
      this.isRecording = true;
      this.updateRecordButtonUI();

      console.log('Recording started');
    } catch (error) {
      console.error('Error starting recording:', error);
      alert(
        'Could not access the microphone. Please ensure you have granted permission.',
      );
    }
  }

  /**
   * Stop recording audio
   */
  stopRecording() {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
      this.isRecording = false;
      this.updateRecordButtonUI();

      // Stop all tracks on the stream
      if (this.stream) {
        this.stream.getTracks().forEach((track) => track.stop());
      }

      console.log('Recording stopped');
    }
  }

  /**
   * Process the recorded audio and convert it to text
   */
  async processAudio() {
    if (this.audioChunks.length === 0) {
      console.warn('No audio recorded');
      return;
    }

    try {
      // Show processing status
      this.transcriptionStatusElement.classList.remove('hidden');
      this.transcriptionStatusElement.textContent = 'Processing audio...';

      // Create audio blob
      const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });

      // Create form data for API request
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');

      // Send to backend for transcription
      const response = await fetch('/api/transcribe/', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(
          `Server responded with ${response.status}: ${response.statusText}`,
        );
      }

      const result = await response.json();

      // Update textarea with transcription
      if (result.text) {
        this.textareaElement.value = result.text;
        this.saveButtonElement.disabled = false;
      } else {
        this.textareaElement.value = 'Sorry, no transcription was returned.';
      }

      // Hide processing status
      this.transcriptionStatusElement.classList.add('hidden');
    } catch (error) {
      console.error('Error processing audio:', error);
      this.transcriptionStatusElement.textContent =
        'Error processing audio. Please try again.';
      setTimeout(() => {
        this.transcriptionStatusElement.classList.add('hidden');
      }, 3000);
    }
  }

  /**
   * Update the record button UI based on recording state
   */
  updateRecordButtonUI() {
    if (this.recordButtonElement) {
      if (this.isRecording) {
        this.recordButtonElement.innerHTML = `
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"></path>
          </svg>
          Stop Recording
        `;
        this.recordButtonElement.classList.remove('bg-red-600');
        this.recordButtonElement.classList.add('bg-gray-600');
      } else {
        this.recordButtonElement.innerHTML = `
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path>
          </svg>
          Start Recording
        `;
        this.recordButtonElement.classList.remove('bg-gray-600');
        this.recordButtonElement.classList.add('bg-red-600');
      }
    }
  }

  /**
   * Save the transcription to the input field
   */
  saveTranscription() {
    const transcriptionText = this.textareaElement.value.trim();
    if (transcriptionText) {
      // Find the message input field
      const messageInput = document.querySelector('input[name="message"]');
      if (messageInput) {
        // Set the value in the input field (using Alpine.js x-model)
        const messageModel = messageInput.getAttribute('x-model');
        if (messageModel) {
          // Use Alpine.js to set the value
          window.Alpine.evaluate(
            messageInput,
            `${messageModel} = "${transcriptionText.replace(/"/g, '\\"')}"`,
          );
        }
      }

      // Hide the modal
      this.hideModal();
    }
  }
}

// Initialize voice transcription when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  const voiceTranscription = new VoiceTranscription();
  voiceTranscription.init();
});
