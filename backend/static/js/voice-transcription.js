// Voice Transcription using the Web Speech API
document.addEventListener('alpine:init', () => {
  Alpine.data('voiceTranscription', () => ({
    isRecording: false,
    transcription: '',
    recognition: null,
    showModal: false,

    init() {
      // Check if SpeechRecognition is supported
      if (
        !('webkitSpeechRecognition' in window) &&
        !('SpeechRecognition' in window)
      ) {
        console.error('Speech recognition is not supported in this browser');
        return;
      }

      // Initialize SpeechRecognition
      this.recognition = new (window.SpeechRecognition ||
        window.webkitSpeechRecognition)();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = 'en-US'; // Default language

      // Handle results
      this.recognition.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        // Update transcription
        this.transcription = finalTranscript || interimTranscript;
      };

      // Handle errors
      this.recognition.onerror = (event) => {
        console.error('Speech recognition error', event.error);
        this.stopRecording();
      };

      // Handle end of recording
      this.recognition.onend = () => {
        // Only stop the recording if it was intentionally stopped
        if (this.isRecording) {
          this.isRecording = false;
        }
      };
    },

    toggleRecording() {
      if (this.isRecording) {
        this.stopRecording();
      } else {
        this.startRecording();
      }
    },

    startRecording() {
      this.isRecording = true;
      this.recognition.start();
    },

    stopRecording() {
      this.isRecording = false;
      this.recognition.stop();
    },

    insertTranscription() {
      // Get the text input element
      const messageInput = document.querySelector('input[name="message"]');
      if (messageInput && this.transcription) {
        // Set the value through Alpine.js
        const messageInputComponent = Alpine.$data(
          messageInput.closest('[x-data]'),
        );
        if (messageInputComponent) {
          messageInputComponent.message = this.transcription;
        }
      }

      this.closeModal();
    },

    closeModal() {
      this.showModal = false;
      this.stopRecording();
      this.transcription = '';
    },

    openModal() {
      this.showModal = true;
      this.transcription = '';
    },
  }));
});

// Initialize the voice record button
document.addEventListener('DOMContentLoaded', () => {
  // Add a small delay to ensure Alpine is fully initialized
  setTimeout(() => {
    const voiceRecordButton = document.getElementById('voice-record');

    if (voiceRecordButton) {
      voiceRecordButton.addEventListener('click', () => {
        // Find the Alpine component
        const modal = document.querySelector('[x-data="voiceTranscription"]');
        if (modal) {
          // Access the Alpine component using Alpine.$data
          const component = Alpine.$data(modal);
          if (component) {
            component.openModal();
          } else {
            console.error('Could not get Alpine component data');
          }
        } else {
          console.error('Voice transcription modal not found');
        }
      });
    } else {
      console.error('Voice record button not found');
    }
  }, 100); // Small delay to ensure Alpine is initialized
});
